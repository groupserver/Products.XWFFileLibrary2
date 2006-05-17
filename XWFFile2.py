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
import os

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.XWFCore import XWFUtils

from AccessControl import getSecurityManager, ClassSecurityInfo
from Globals import InitializeClass, PersistentMapping
from OFS.Image import File, Pdata
from Products.CustomProperties.CustomProperties import CustomProperties
from Products.ZCatalog.CatalogPathAwareness import CatalogAware
from Products.XWFCore import IXWFXml
from types import *
from Acquisition import aq_base, aq_parent, aq_inner, aq_acquire

from zope.interface import implements
from Products.XWFFileLibrary2.interfaces import IXWFFile2

from mimetypes import MimeTypes

from zLOG import LOG, INFO

import xml.sax, cgi
import zipfile, cStringIO, string
from xml.sax.handler import ContentHandler

class ootextHandler(ContentHandler):

    def characters(self, ch):
        self._data.write(ch.encode("utf-8") + ' ')

    def startDocument(self):
        self._data = cStringIO.StringIO()

    def getxmlcontent(self, doc):

        file = cStringIO.StringIO(doc)

        doctype = """<!DOCTYPE office:document-content PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "office.dtd">"""
        xmlstr = zipfile.ZipFile(file).read('content.xml')
        xmlstr = xmlstr.replace(doctype,'')
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
    LOG('XWFFile2',INFO,'we are %s' % str(ob.getId()))

    if event.newParent.meta_type != 'XWF File Storage 2':
        return

    ob._base_files_dir = event.newParent.get_baseFilesDir()

def removedFile(ob, event):
    """ A File was removed from the storage.

    """
    filepath = os.path.join(ob._base_files_dir, ob.getId())
    LOG('XWFFile2',INFO,'removed file %s' % filepath)
    os.remove(filepath)

from zope.app.container.interfaces import IObjectRemovedEvent,IObjectAddedEvent
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
    
    __implements__ = (IXWFXml.IXmlProducer,)
    implements(IXWFFile2)

    meta_type = 'XWF File 2'
    version = 0.1
    
    # base files dir
    _base_files_dir = ''
    
    converters = {'application/vnd.oasis.opendocument.spreadsheet': (OOfficeConverter(), 'OpenOffice Spreadsheet')}
    
    def __init__(self, id):
        """ Initialise a new instance of XWFFile.
            
        """
        self.id = id
        self.initProperties()
        File.__init__(self, id, id, '', '', '')
        self.update_data('','',0)
    
    def initProperties(self):
        for prop in (('group_ids',[],'lines'),
                     ('topic', '', 'ustring'),
                     ('tags', [], 'ulines'),
                     ('dc_creator', '', 'ustring'),
                     ('description', '', 'ustring')):
            self.manage_addProperty(*prop)
    
    def _renderPageTemplateFile(self, filename, *args, **kws):
        """ Render a page template file, handling all the weird magic for us.
         
        """
        return apply(PageTemplateFile(filename,
                                      globals()).__of__(self),
                     args,
                     kws)   

    def get_xml(self):
        """ Get an XML representation of the file object.
        
        """
        xml_stream = ['<%s:file id="%s" ' % (self.default_nsprefix,
                                             self.getId())]
        xa = xml_stream.append
        
        prefixnsmap = self.get_metadataFullPrefixNSMap()
        
        for prefix in prefixnsmap.keys():
            ns = prefixnsmap[prefix]
            if not prefix: prefix = self.default_nsprefix
            
            xa('xmlns:%s="%s"' % (prefix,ns))
        xa('>')
        xa(self.get_xmlMetadataElements(self.default_nsprefix))
        
        xa('</%s:file>' % self.default_nsprefix)
    
        return '\n'.join(xml_stream)
        
    def get_xmlMetadataElements(self, default_ns=''):
        """ 
        
        """
        xml_stream = []
        element_template = '<%(metadata_id)s>%(metadata_value)s</%(metadata_id)s>'
        # fetch the dict of all possible metadata types in this filelibrary
        metadata_set = self.get_metadataIndexMap()
        for key in metadata_set.keys():
            value = getattr(self, key, None) or self.getProperty(key, None) 
            if value:
                if callable(value):
                    value = value()
                if default_ns and len(key.split('+')) == 1:
                    key = '%(default_ns)s:%(key)s' % locals()
                
                if type(value) in (ListType, TupleType):
                    values = value
                else:
                    values = (str(value),)
                
                for val in values:
                    if not val: continue
                    key = ':'.join(key.split('+'))
                    xml_stream.append(element_template % {'metadata_id': key,
                                                          'metadata_value': val})
        return '\n'.join(xml_stream)
        
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
        # this isn't necessarily an error, on init we get called without data
        base_files_dir = self._base_files_dir
        self.size = size
        self.set_modificationTime()
        
        if base_files_dir:
            id = os.path.join(base_files_dir, self.getId())
            f = file(id, 'wb+')
        
            if hasattr(data, '__class__') and data.__class__ is Pdata:
                while data is not None:
                    f.write(data.data)
                    data=data.next
            else:
                f.write(data)
            
            f.close()
        
        # fix the title
        title = self.title
        tbits = title.split('/')
        title = ''.join(tbits[-1])
        
        self.title = title
        
        if content_type != None:
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
        
    def read(self, file_only=False):
        """ Read back the file data from our backend.
            
            This just returns the data, it doesn't do _anything_ tricky,
            like setting HTTP headers, or getting ranges from the file.
        
        """
        id = os.path.join(self._base_files_dir, self.getId())
        
        try:
            f = file(id)
        except:
            return ''
        
        if file_only:
            return f
        
        return f.read()
    
    @property
    def data(self):
        """  """
        data, size = self._read_data(self.read(file_only=False))
        
        return data
    
    def modification_time(self):
        """ Return the modification time.
        
        """
        if hasattr(self, '_modification_time'):
            return self._modification_time
            
        return self.bobobase_modification_time()
    
    def indexable_content(self, escape=True):
        """ Returns the content as bare as possible for indexing.
        
        Trim to 5kB -- this means we don't index the _whole_ document
        necessarily, but then we probably don't blow our DB out either.
        
        """
        converters = self.converters.get(getattr(self.aq_explicit, 'content_type', ''), (None, None))
        if converters[0]:
            data, encoding = converters[0].convert(self.data)[:5000]
            if encoding != 'UTF-8':
                data = data.decode(encoding).encode('UTF-8')
        else:
            data = self.data[:10000]
        
            data = XWFUtils.convertTextToAscii(data)
            
            try:
                data = str(data.decode('UTF-8'))
            except:
                data = ''
        
        if escape:
            return cgi.escape(data)
        
        new_data = []
        for word in data.split():
            if len(word) > 15:
                continue
            
            for letter in word:
                if letter not in string.letters:
                    continue
 
            new_data.append(word)
            
        data = ' '.join(new_data)

        return data
        
    #def summary(self):
    #    """ Returns a shortened version of indexable_content for use
    #    in the catalog metadata summary of a file.
    #    
    #    Basically we return either up to 500 characters or up to 50 words.
    #    
    #    """
    #    content = self.indexable_content(escape=False)[:500]
    #    words = content.split()
    #    
    #    strippedwords = ''
    #    count = 0
    #    for word in words:
    #        if len(word) <= 25:
    #            strippedwords += '%s ' % word
    #    
    #    return cgi.escape(strippedwords)
    
    # for now we just use the description property, rather than trying to be 
    # tricky
    def indexable_summary(self):
        """ Return a summary for indexing in the catalog.

        """
        return self.getProperty('description', '')
    
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

def manage_addXWFFile2(container, id, file_object,
                             REQUEST=None, RESPONSE=None, submit=None):
    """ Add a new instance of XWFFile.
        
        UnitTest: TestXWFFileLibrary
    """
    obj = XWFFile2(id)
    container._setObject(id, obj)
    
    obj = getattr(container, id)
    
    obj.manage_upload(file_object)
    
    if RESPONSE and submit:
        if submit.strip().lower() == 'add':
            RESPONSE.redirect('%s/manage_main' % self.DestinationURL())
        else:
            RESPONSE.redirect('%s/manage_main' % id)

def initialize(context):
    context.registerClass(
        XWFFile2,
        permission='Add XWF File',
        constructors=(manage_addXWFFile2Form,
                      manage_addXWFFile2),
        icon='icons/ic-filelibrary.png'
        )

