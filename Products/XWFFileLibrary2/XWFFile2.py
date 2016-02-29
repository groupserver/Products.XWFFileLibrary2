# Copyright (C) 2003,2004 IOPEN Technologies Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# You MUST follow the rules in http://iopen.net/STYLE before checking in code
# to the trunk. Code which does not follow the rules will be rejected.
#
import cgi
import cStringIO
from mimetypes import MimeTypes
import os
import string
import tempfile
# from types import *
import xml.sax
import zipfile
from xml.sax.handler import ContentHandler

#lint:disable
try:
    # 2.12+
    from zope.container.interfaces import IObjectRemovedEvent, \
        IObjectAddedEvent
except ImportError:
    from zope.app.container.interfaces import IObjectRemovedEvent, \
        IObjectAddedEvent
#lint:enable

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.Image import File, Pdata
from Products.ZCatalog.CatalogPathAwareness import CatalogAware
from Products.XWFCore.XWFUtils import removePathsFromFilenames
from Products.XWFCore import XWFUtils
from zope.interface import implements
from Products.XWFFileLibrary2.interfaces import IXWFFile2

import logging
log = logging.getLogger('XWFFile2')


class XWFFileError(Exception):
    pass


class DataVirusCheckClamAVAdapter(object):

    def __init__(self, data):
        self.data = data

    def process(self):
        try:
            fn = tempfile.mktemp()
            f = file(fn, 'a+')
            if hasattr(self.data, '__class__') and self.data.__class__ is Pdata:
                while self.data is not None:
                    f.write(self.data.data)
                    self.data = self.data.next
            else:
                f.write(self.data)

            f.close()

            has_virus, virus_name = pyclamav.scanfile(fn)

        finally:
            os.remove(fn)

        if has_virus:
            return (False, "Found virus %s in file data" % virus_name)

        return (True, '')


class DataVirusCheckNullAdapter(object):
    def __init__(self, data):
        self.data = data

    def process(self):
        return (True, '')

try:
    import pyclamav
    DataVirusCheckAdapter = DataVirusCheckClamAVAdapter
    log.info('found pyclamav, using clam av virus check adapter')
except:
    DataVirusCheckAdapter = DataVirusCheckNullAdapter
    log.warn('pyclamav not found, using null virus check adapter')


class ootextHandler(ContentHandler):

    def characters(self, ch):
        self._data.write(ch.encode("utf-8") + ' ')

    def startDocument(self):
        self._data = cStringIO.StringIO()

    def getxmlcontent(self, doc):

        f = cStringIO.StringIO(doc)

        doctype = '<!DOCTYPE office:document-content PUBLIC '\
            '"-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "office.dtd">'
        xmlstr = zipfile.ZipFile(f).read('content.xml')
        xmlstr = xmlstr.replace(doctype, '')
        return xmlstr

    def getData(self):
        return self._data.getvalue()


class OOfficeConverter:
    def convert(self, doc):
        handler = ootextHandler()
        xmlstr = handler.getxmlcontent(doc)
        xml.sax.parseString(xmlstr, handler)
        return handler.getData(), 'utf-8'


def addedFile(ob, event):
    """A File was added to the storage.

    """
    if event.newParent.meta_type != 'XWF File Storage 2':
        return

    ob._base_files_dir = event.newParent.get_baseFilesDir()


def removedFile(ob, event):
    """ A File was removed from the storage.

    """
    filepath = os.path.join(ob._base_files_dir, ob.getId())
    try:
        os.remove(filepath)
    except OSError:
        msg = 'Ignoring deletion of non-existant file "{0}".'.format(filepath)
        log.warn(msg)


def movedFile(ob, event):
    """A File was moved in the storage.

    """
    if not IObjectRemovedEvent.providedBy(event):
        #raise NotImplementedError # we don't support moving
        return
    if not IObjectAddedEvent.providedBy(event):
        removedFile(ob, event)


def copiedFile(ob, event):
    """A File was copied.

    """
    # We don't support this
    raise NotImplementedError


class XWFFile2(CatalogAware, File):
    """ The basic implementation for a file object, with metadata stored in
    the ZODB, and the data stored on disk.

    """
    security = ClassSecurityInfo()
    implements(IXWFFile2)
    manage_options = File.manage_options + \
        ({'label': 'Reindex', 'action': 'reindex_file'},)
    meta_type = 'XWF File 2'
    version = 0.1
    # base files dir
    _base_files_dir = ''
    converters = {'application/vnd.oasis.opendocument.spreadsheet':
                  (OOfficeConverter(), 'OpenOffice Spreadsheet')}

    def __init__(self, id):
        """ Initialise a new instance of XWFFile.

        """
        self.id = id
        self.initProperties()
        File.__init__(self, id, id, '', '', '')
        self.update_data('', '', 0)

    def initProperties(self):
        for prop in (('group_ids', [], 'lines'),
                     ('topic', '', 'ustring'),
                     ('tags', [], 'ulines'),
                     ('dc_creator', '', 'ustring'),
                     ('description', '', 'ustring'),
                     ('content-type', '', 'ustring')):
            self.manage_addProperty(*prop)

    def index_html(self, REQUEST, RESPONSE):
        """ Override for File.index_html
        """
        # this is to deal with an acquisition issue, where
        # the context gets lost when .data is called
        bfd = self.get_baseFilesDir()
        if self._base_files_dir != bfd:
            self._base_files_dir = bfd

        return File.index_html(self, REQUEST, RESPONSE)

    def _renderPageTemplateFile(self, filename, *args, **kws):
        """ Render a page template file, handling all the weird magic for us.

        """
        return apply(PageTemplateFile(filename, globals()).__of__(self), args, kws)

    def write(self, file_object):
        """ Write the file data to our backend, given an object with a 'file'
        like interface (primarily it must support the 'read' interface).

            Offers a simpler interface than the 'update_data', and a more
            obvious interface than manage_upload.
        """
        self.manage_upload(file_object)

    def update_data(self, data, content_type, size):
        """

        """
        if not data:
            # still index
            self.index_object()
            return

        passed, virus_name = DataVirusCheckAdapter(data).process()

        if not passed:
            log.warn('found virus %s, rejecting file' % virus_name)
            raise XWFFileError('found virus %s, rejecting file' % virus_name)

        # this isn't necessarily an error, on init we get called without data
        base_files_dir = self._base_files_dir
        self.size = size
        self.set_modificationTime()

        if base_files_dir:
            fileId = os.path.join(base_files_dir, self.getId())
            f = file(fileId, 'wb+')

            if hasattr(data, '__class__') and data.__class__ is Pdata:
                while data is not None:
                    f.write(data.data)
                    data = data.next
            else:
                f.write(data)

            f.close()

        # fix the title
        title = self.title
        title = unicode(title, 'UTF-8', 'ignore')
        title = removePathsFromFilenames(title)
        self.title = title

        if content_type is not None:
            self.content_type = content_type
        else:
            mtypes = MimeTypes()
            mime_type = mtypes.guess_type(title)
            if mime_type:
                self.content_type = mime_type

        self.ZCacheable_invalidate()
        self.ZCacheable_set(None)
        self.http__refreshEtag()

        # index ourselves into the catalog
        self.index_object()

    def reindex_file(self):
        """ Reindex ourselves into the catalog.

        """
        self.reindex_object()

        return 'Successfully reindexed file'

    def read(self, file_only=False):
        """ Read back the file data from our backend.

            This just returns the data, it doesn't do _anything_ tricky,
            like setting HTTP headers, or getting ranges from the file.

        """
        log.debug("Reading file from backend\n")
        fileId = os.path.join(self._base_files_dir, self.getId())
        try:
            f = file(fileId)
        except:
            return ''

        if file_only:
            return f

        return f.read()

    @property
    def data(self):
        """  """
        return self.read(file_only=False)

    def modification_time(self):
        """ Return the modification time.

        """
        if hasattr(self, '_modification_time'):
            return self._modification_time

        return self.bobobase_modification_time()

    def indexable_content(self, escape=True):
        """ Returns the content as bare as possible for indexing.

        Trim to 3kB -- this means we don't index the _whole_ document
        necessarily, but then we probably don't blow our DB out either.

        """
        c = getattr(self.aq_explicit, 'content_type', '')
        converters = self.converters.get(c, (None, None))
        if converters[0]:
            data, encoding = converters[0].convert(self.data)
            if encoding != 'UTF-8':
                data = unicode(data, 'UTF-8', 'ignore')
        else:
            data = self.data[:5000]

            data = XWFUtils.convertTextToAscii(data)

            try:
                data = unicode(data, 'UTF-8', 'ignore')
            except:
                data = u''

        data = data[:3000]

        new_data = []
        for word in data.split():
            if len(word) > 15 or len(word) < 3:
                continue

            skip = False
            for letter in word:
                if letter not in string.letters:
                    skip = True
                    break

            if not skip:
                new_data.append(word)

        data = ' '.join(new_data)

        if escape:
            return cgi.escape(data)

        return data

    # for now we just use the description property, rather than trying to be
    # tricky
    def indexable_summary(self):
        """ Return a summary for indexing in the catalog.

        """
        description = self.getProperty('description', u'')
        if not isinstance(description, unicode):
            description = unicode(description, 'UTF-8', 'ignore')

        return description

    summary = indexable_summary

    def set_modificationTime(self, time=None):
        """ Set the modification time.

            Takes either a datetime object, or a date/time string.
        """
        import DateTime

        if not time:
            self._modification_time = DateTime.DateTime()
        else:
            # by marshalling the time to a string, we can be reasonably
            # sure that DateTime will be able to deal with it, even if it
            # was a DateTime object to begin with.
            self._modification_time = DateTime.DateTime(str(time))

        return self._modification_time

InitializeClass(XWFFile2)
#
# Zope Management Methods
#
manage_addXWFFile2Form = PageTemplateFile(
    'management/manage_addXWFFileForm.zpt',
    globals(), __name__='manage_addXWFFile2Form')


def manage_addXWFFile2(container, fileId, file_object, REQUEST=None, RESPONSE=None, submit=None):
    """ Add a new instance of XWFFile.

        UnitTest: TestXWFFileLibrary
    """
    obj = XWFFile2(fileId)
    container._setObject(fileId, obj)

    obj = getattr(container, fileId)

    if file_object:
        obj.manage_upload(file_object)

    if RESPONSE and submit:
        if submit.strip().lower() == 'add':
            RESPONSE.redirect('%s/manage_main' % obj.DestinationURL())
        else:
            RESPONSE.redirect('%s/manage_main' % fileId)


def initialize(context):
    context.registerClass(
        XWFFile2,
        permission='Add XWF File',
        constructors=(manage_addXWFFile2Form,
                      manage_addXWFFile2),
        icon='icons/ic-filelibrary.png')
