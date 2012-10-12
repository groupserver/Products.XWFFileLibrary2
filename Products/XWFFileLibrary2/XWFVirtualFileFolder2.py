# coding=utf-8
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
import types

from App.class_init import InitializeClass

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from XWFFile2 import XWFFileError

from DateTime import DateTime
from AccessControl import getSecurityManager, ClassSecurityInfo
from types import * #@UnusedWildImport
import os
from OFS.Folder import Folder
from Products.XWFCore.XWFUtils import removePathsFromFilenames, convertTextToAscii
from Products.XWFCore.XWFUtils import convertTextToId, getNotificationTemplate
from gs.image import GSImage

from zExceptions import Unauthorized
from zope.app.file.image import Image, getImageInfo

from zope.interface import implements
from zope.publisher.browser import BrowserView
from zope.app.file.browser.file import FileView

from interfaces import IXWFVirtualFileFolder
from queries import FileQuery
from error import Hidden
from zope.component import getMultiAdapter
from zope.publisher.interfaces import NotFound

import logging
log = logging.getLogger('XWFFileLibrary2.XWFVirtualFileFolder2')

_marker = []

class DisplayFile(FileView, BrowserView):
    pass

class XWFVirtualFileFolderError(Exception):
    pass

class XWFVirtualFileFolder2(Folder):
    """ A folder for virtualizing file library content.

        When content is 'added' to a 'VirtualFileFolder' the content object
        is cataloged with the appropriate 'virtual_path', and the
        'VirtualFileFolder' knows how to find XWF content that has been placed
        inside itself.

    """
    implements( IXWFVirtualFileFolder )
    security = ClassSecurityInfo()

    meta_type = 'XWF Virtual Folder 2'
    version = 0.1

    manage_options = Folder.manage_options + \
                     ({'label': 'Configure',
                       'action': 'manage_configure'},)

    printable_mimetypes = ('application/vnd.oasis.opendocument.spreadsheet',
                           'text/plain')

    xwf_file_library_path = 'FileLibrary2'

    public_access_period = 259200

    default_nsprefix = 'file'

    _properties=(
        {'id':'title', 'type':'string', 'mode':'w'},
        {'id':'id_factory', 'type':'string', 'mode':'w'},
        {'id':'xwf_file_library_path', 'type':'string', 'mode':'w'},
        {'id':'ucid', 'type':'string', 'mode':'w'},
        {'id':'public_access_period', 'type':'int', 'mode':'w'}
        )

    def __init__(self, id, title=None):
        """ Initialise a new instance of XWFVirtualFileFolder.

        """
        self.__name__ = id
        self.id = id
        self.title = title or id
        self.ucid = None

        # period in seconds, defaults to 72 hours
        self.public_access_period = 259200

    def __before_publishing_traverse__(self, self2, request):
        """ """
        path = request['TraversalRequestNameStack']
        subpath = path[:]
        subpath.reverse()
        if subpath:
            path[:] = [subpath[0]]
        else:
            path[:] = []
        request.set('traverse_subpath', subpath)

    def processForm(self):
        """ Process an XForms submission.

        """
        result = {}

        form = self.REQUEST.form
        result['form'] = form

        if not form.get('submitted', False):
            return result

        submit = form.get('__submit__')
        model, submission = submit.split('+')
        model = form.get('model_override', model)

        cb = getattr(self, 'cb_%s_%s' % (model,submission))

        return cb(form)

    def get_xwfFileLibrary(self):
        """ Get the reference to the xwfFileLibrary we are associated with.

        """
        library = self.restrictedTraverse(self.xwf_file_library_path)

        return library

    security.declareProtected('View', 'find_files')
    def find_files(self, query={}):
        """ Perform a search against the files associated with this
            VirtualFileFolder.

            Takes:
              query: a catalog query dictionary.

           The results returned act as a lazy sequence, from the ZCatalog.Lazy
           module, so it is possible to slice the returned sequence in order to
           limit the result set.

           It is possible to sort the result set using the sort_on, sort_order
           and sort_limit index names in the query dictionary. See the ZCatalog
           documentation for further information on the query dictionary.

        """
        library = self.get_xwfFileLibrary()

        # group_object = self.Scripts.get.group_object()
        group_object = self.aq_parent
        group_ids = group_object and [group_object.getId()] or []

        query['group_ids'] = group_ids

        results = library.find_files(query)

        return results

    def fileQuery(self):
        context = self.get_xwfFileLibrary()
        retval = FileQuery(context)
        assert retval
        return retval

    security.declarePublic('get_file')
    def get_file(self, REQUEST=None, RESPONSE=None, data_only=False):
        """ """
        if REQUEST.get('REQUEST_METHOD') == 'OPTIONS':
            return self.OPTIONS(REQUEST, RESPONSE)
        elif REQUEST.get('REQUEST_METHOD') == 'PROPFIND':
            return self.PROPFIND(REQUEST, RESPONSE)

        fileId = REQUEST.form.get('id', '')
        files = self.find_files({'id': fileId})
        if files:
            fileObject = files[0].getObject()
            modification_time = fileObject.modification_time()
            # transform period from seconds into days
            p = getattr(self, 'public_access_period', 0)
            public_access_period = float(p) / 86400.0

            if DateTime() < (modification_time + public_access_period):
                public_access = True
            else:
                public_access = False
        else:
            fileObject = None
            public_access = False

        access = getSecurityManager().checkPermission('View', self)
        if ((not public_access) and (not access)):
            raise Unauthorized

        if self.fileQuery().file_hidden(fileId):
            raise Hidden(fileId)
        # assert ((public_access or access) and not(hidden))

        if fileObject:
            # we call the index_html method of the file object, because
            # that will handle all the nice things, like setting the
            # correct content_type. It doesn't set the correct filename
            # though, so we do that first.
            filename = fileObject.getProperty('filename', '').strip()
            if not filename:
                filename = fileObject.getProperty('title')
            self.REQUEST.RESPONSE.setHeader('Content-Disposition',
                                            'inline; filename="%s"' %
                                            filename)
            # if we can use sendfile, we use that instead of returning
            # the file through Zope
            sendfile_header = self.get_xsendfile_header(REQUEST, RESPONSE)
            if sendfile_header and not data_only:
                log.debug('Using x-sendfile')
                file_path = os.path.join(fileObject.get_baseFilesDir(),
                                         fileObject.getId())
                RESPONSE.setHeader('Content-Type', fileObject.content_type)
                RESPONSE.setHeader(sendfile_header,
                                   file_path)
                # return *something* otherwise Apache mod_sendfile chokes
                return fileObject.content_type
            # not(sendfile_header) or data_only
            # --=mpj17=-- I do not pretend to understand what is going
            #   on in this method. However, I do know that sometimes the
            #   "index_html" is false (with a small f) when the cast of
            #   the "object" to a string *is* data. Is this a security
            #   hole?
            return fileObject.index_html(REQUEST, RESPONSE) or str(fileObject)
        else:
            # We could not find the file
            uri = '/r/file-not-found?id=%s' % fileId
            return self.REQUEST.RESPONSE.redirect(uri)
        assert False, 'How did I get here?'

    def get_xsendfile_header(self, REQUEST, RESPONSE):
        sendfile_header = None
        if REQUEST.has_key('X-Sendfile-Type'):
            sendfile_header = REQUEST.get('X-Sendfile-Type')
        elif REQUEST.has_key('HTTP_X_SENDFILE_TYPE'):
            sendfile_header = REQUEST.get('HTTP_X_SENDFILE_TYPE')

        return sendfile_header

    security.declarePublic('f')
    def f(self, REQUEST, RESPONSE):
        """ A really short name for a file, enabling fetching a file like:

               /SOMEFILESAREA/f/FILEID/FILE_NAME

            Security is effectively handed off to get_file, so use extreme
            caution.

            Images may also be handled like this:

              /SOMEFILESAREA/f/FILEID/resize/WIDTH/HEIGHT/FILE_NAME

            eg.
              /myfilearea/f/12211/resize/640/480/myimg.jpg

        """
        tsp = REQUEST.traverse_subpath

        fid = tsp[1]
        # a workaround for an odd bug
        if fid == 'f':
            fid = tsp[2]
            tsp.pop(1)

        REQUEST.form['id'] = fid

        try:
            if len(tsp) in (5, 6) and tsp[2] == 'resize':
                # we set data_only=True in case the backend uses sendfile
                data = self.get_file(REQUEST, RESPONSE, data_only=True)
            else:
                data = self.get_file(REQUEST, RESPONSE)
        except Hidden, h:  # lint:ok
            # --=mpj17=-- The post that includes this file is hidden.
            # By extension, this means the file is hidden. We *could*
            # just pass up a zExceptions.Unauthorized error up, but
            # that error would confuse the admins. Instead we will show
            # a page that explains what is going on.
            self.REQUEST.form['q'] = self.REQUEST.URL
            self.REQUEST.form['f'] = self.REQUEST.form.get('id', '')
            ctx = self.aq_parent.files
            #ctx = self.Scripts.get.group_object().files
            retval = getMultiAdapter((ctx, self.REQUEST),
                                        name="file_hidden.html")()
            return retval

        if not data:
            log.warn("No data found for %s." % fid)
            raise NotFound(self, fid, self.REQUEST)

        if len(tsp) in (5, 6) and tsp[2] == 'resize':
            width, height = int(tsp[3]), int(tsp[4])
            content_type, img_width, img_height = getImageInfo(data)
            if content_type and width == img_width and height == img_height:
                log.debug("Not resizing image, existing height and width "
                         "were the same as requested size")
            # test that we're really an image
            elif content_type:
                # if we can use sendfile, we use that instead of returning
                # the file through Zope
                sendfile_header = self.get_xsendfile_header(REQUEST, RESPONSE)

                if sendfile_header:
                    log.debug('Using x-sendfile')
                    # if we are going to use sendfile, we can either
                    # return the cached image, or return the original image,
                    # depending on whether we actually resized it
                    cache_path = GSImage(data).get_resized(width, height,
                                                    return_cache_path=True)
                    if cache_path:
                        RESPONSE.setHeader(sendfile_header,
                                           cache_path)
                        data = 'image'
                    else:
                        data = self.get_file(REQUEST, RESPONSE)
                else:
                    img = GSImage(data).get_resized(width,height)
                    if img:
                        data = DisplayFile(img, REQUEST).show()
                    else:
                        data = self.get_file(REQUEST, RESPONSE)
        return data

    security.declareProtected('View', 'hide_file')
    def hide_file(self, id):
        """ """
        object = self.find_files({'id': id})[0].getObject()

        tags = list(object.getProperty('tags', []))
        if 'hidden' not in tags:
            tags.append('hidden')

        object.manage_changeProperties(tags=tags)
        object.reindex_object()

        return 'Hidden %s' % id

    security.declareProtected('View', 'show_file')
    def show_file(self, id):
        """ """
        object = self.find_files({'id': id})[0].getObject()

        tags = list(object.getProperty('tags', []))
        if 'hidden' in tags:
            tags.remove('hidden')

        object.manage_changeProperties(tags=tags)
        object.reindex_object()

        return 'Shown %s' % id

    security.declarePublic('OPTIONS')
    def OPTIONS(self, REQUEST, RESPONSE):
        """ Retrieve communication options.

            We disable the publishing of webdav methods.
        """
        self.dav__init(REQUEST, RESPONSE)
        RESPONSE.setHeader('Allow', ', '.join(('GET','HEAD','POST')))
        #RESPONSE.setHeader('Allow', ', '.join(self.__http_methods__))
        RESPONSE.setHeader('Content-Length', 0)
        #RESPONSE.setHeader('DAV', '1,2', 1)
        RESPONSE.setStatus(200)
        return ''

    security.declarePublic('PROPFIND')
    def PROPFIND(self, REQUEST, RESPONSE):
        """ We don't support webdav, at all!

        """
        from zExceptions import MethodNotAllowed
        raise MethodNotAllowed, ('Method not supported for this resource.')

    def pretty_size(self, size):
        """ Given a size, return a 'prettied' variation that most users will
        understand.

        """
        if size < 5000:
            return 'tiny'
        elif size < 1000000:
            return '%sKB' % (size/1024)
        else:
            return '%sMB' % (size/(1024*1024))

    def printable_summary(self, result):
        """ Given a result, determine if the summary is actually printable or
        not. If so, return the summary, otherwise return None.

        """
        return result.indexable_summary

InitializeClass(XWFVirtualFileFolder2)
#
# Zope Management Methods
#
manage_addXWFVirtualFileFolder2Form = PageTemplateFile(
    'management/manage_addXWFVirtualFileFolderForm.zpt',
    globals(), __name__='manage_addXWFVirtualFileFolder2Form')

def manage_addXWFVirtualFileFolder2(self, id, title='',
                               REQUEST=None, RESPONSE=None, submit=None):
    """ Add a new instance of XWFVirtualFileFolder

    """
    id = convertTextToId(id)
    title = convertTextToAscii(title) or convertTextToAscii(id)
    obj = XWFVirtualFileFolder2(id, title)
    self._setObject(id, obj)

    obj = getattr(self, id)

    if RESPONSE and submit:
        if submit.strip().lower() == 'add':
            RESPONSE.redirect('%s/manage_main' % self.DestinationURL())
        else:
            RESPONSE.redirect('%s/manage_main' % id)

def initialize(context):
    context.registerClass(
        XWFVirtualFileFolder2,
        permission='Add XWF Virtual Folder 2',
        constructors=(manage_addXWFVirtualFileFolder2Form,
                      manage_addXWFVirtualFileFolder2),
        icon='icons/ic-virtualfolder.png'
        )
