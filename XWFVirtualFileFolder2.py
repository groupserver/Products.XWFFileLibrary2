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
import Globals, types

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.XWFIdFactory.XWFIdFactoryMixin import XWFIdFactoryMixin
from XWFFile2 import XWFFileError

from DateTime import DateTime        
from AccessControl import getSecurityManager, ClassSecurityInfo
from types import * #@UnusedWildImport
from OFS.Folder import Folder
from Products.XWFCore.XWFUtils import removePathsFromFilenames, convertTextToAscii
from Products.XWFCore.XWFUtils import convertTextToId, getNotificationTemplate
from Products.GSImage.interfaces import IGSImage

from zExceptions import Unauthorized        
from OFS.Image import Image, getImageInfo

from zope.interface import implements
from interfaces import IXWFVirtualFileFolder

import logging
log = logging.getLogger('XWFFileLibrary2.XWFVirtualFileFolder2')

_marker = []

class XWFVirtualFileFolderError(Exception):
    pass

class XWFVirtualFileFolder2(Folder, XWFIdFactoryMixin):
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

    id_factory = 'IdFactory'
    id_namespace = 'http://xwft.org/namespaces/xwft/virtualfolder'
    public_access_period = 0

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
        self.public_access_period = 0 # never publicly accessible, period is in seconds

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

    def add_file(self, file_object, properties={}):
        """ Add a file to the appropriate file library, returning a
        reference to the file for further manipulation, after we add ourselves
        to the files virtual path.
        
        """
        library = self.get_xwfFileLibrary()
        if not library:
            raise XWFVirtualFileFolderError, 'No XWF File Library found'
            
        storage = library.get_fileStorage()
        
        filename = getattr(file_object, 'filename', '')
        fname = convertTextToAscii(removePathsFromFilenames(filename))
        
        id = storage.add_file(file_object, fname)
        
        _file = storage.get_file(id)
                
        group_object = self.Scripts.get.group_object()
        group_ids = group_object and [group_object.getId()] or []
        
        _file.manage_changeProperties(group_ids=group_ids,
                                      title=fname,
                                      **properties)
        _file.reindex_object()
        
        return _file
        
    def send_notification(self, topic='', file=None):
        """ Send a notification to the associated list when a file is 
        added.
        
        """
        security = getSecurityManager()
        user = security.getUser()
        messages = getattr(self.aq_parent, 'messages', None)
        # we don't have an associated messages, so don't send anything
        if not messages:
            return False
        
        if not topic:
            topic = 'A new file was added'
        
        group_object = self.Scripts.get.group_object()
        # we don't actually seem to be a group, so don't send anything
        if not group_object:
            return False
        
        group_id = group_object.getId()

        template = getNotificationTemplate(self, 'new_file', group_id)
        if not template:
            return False
        
        email_addresses = user.get_preferredEmailAddresses()
        if not email_addresses:
            return False
        
        email_address = email_addresses[0]
        
        list_manager = messages.get_xwfMailingListManager()
        for list_id in messages.getProperty('xwf_mailing_list_ids', []):        
            curr_list = list_manager.get_list(list_id)
            message = template(self, self.REQUEST, from_addr=email_address,
                                 n_type='new_file', n_id=group_id,
                                 subject=topic, group=group_object, list_object=curr_list,
                                 user=user, file=file)        
            result = curr_list.manage_listboxer({'Mail': message})
        
        return result
    
    def get_xml(self, set_top=0):
        """ Generate an XML representation of this folder.
        
        """
        num_files = len(self.find_files())
        xml_stream = ['<%s:folder id="%s" %s:top="%s" %s:count="%s"' % (
                                                   self.default_nsprefix,
                                                   self.getId(),
                                                   self.default_nsprefix,
                                                   set_top,
                                                   self.default_nsprefix,
                                                   num_files)]
        xa = xml_stream.append
        xa('>')
        
        xa('</%s:folder>' % self.default_nsprefix)
    
        return '\n'.join(xml_stream)
        
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
        
        group_object = self.Scripts.get.group_object()
        group_ids = group_object and [group_object.getId()] or []
        
        query['group_ids'] = group_ids
        
        results = library.find_files(query)
        
        return results

    security.declarePublic('get_file')
    def get_file(self, REQUEST, RESPONSE):
        """ """
        if REQUEST.get('REQUEST_METHOD') == 'OPTIONS':
            return self.OPTIONS(REQUEST, RESPONSE)
        elif REQUEST.get('REQUEST_METHOD') == 'PROPFIND':
            return self.PROPFIND(REQUEST, RESPONSE)

        id = REQUEST.form.get('id', '')
        files = self.find_files({'id': id})
        if files:
            object = files[0].getObject()
            modification_time = object.modification_time()
            # transform period from seconds into days
            public_access_period = float(getattr(self, 'public_access_period', 0))/86400.0
            
            if DateTime() < (modification_time+public_access_period):
                public_access = True
            else:
                public_access = False
        else:
            object = None
            public_access = False
            
        access = getSecurityManager().checkPermission('View', self)
        if (not public_access) and \
           (not access):
            raise Unauthorized

        if object:
            # we call the index_html method of the file object, because
            # that will handle all the nice things, like setting the
            # correct content_type. It doesn't set the correct filename
            # though, so we do that first.
            filename = object.getProperty('filename', '').strip()
            if not filename:
                filename = object.getProperty('title')
            
            self.REQUEST.RESPONSE.setHeader('Content-Disposition',
                                            'inline; filename="%s"' %\
                                            filename)

            return object.index_html(REQUEST, RESPONSE)            
        else:
            # We could not find the file
            uri = '/r/file-not-found?id=%s' % id
            return self.REQUEST.RESPONSE.redirect(uri)
                    
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
        
        data = self.get_file(REQUEST, RESPONSE)
        
        if len(tsp) in (5,6) and tsp[2] == 'resize':
            width, height = tsp[3], tsp[4]
            content_type, img_width, img_height = getImageInfo(data)
            if content_type and width == img_width and height == img_height:
                log.info("Not resizing image, existing height and width "
                         "were the same as requested size")
            # test that we're really an image
            elif content_type:
                img = Image('img', 'img', data)
                data = IGSImage(img).get_resized(width, height)
                log.info("Resized image")
                
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
                                   
    def cb_file_addFile(self, form):
        topic = form.get('topic', '')
        if type(topic) in (types.TupleType, types.ListType):
            topic = filter(None, topic)
            if not topic:
                topic = ''
            else:
                topic = topic[0]
        
        rtags = form.get('tags', '')
        tagparts = rtags.split('\n')
        tags = []
        for tag in tagparts:
            tags.append(tag.strip().lower())
            
        security = getSecurityManager()
        user = security.getUser()
        if user:
            creator = user.getId()
        else:
            creator = ''
        
        summary = form.get('summary','')

        properties = {'topic': topic,
                      'tags': tags,
                      'dc_creator': creator,
                      'description': summary}
        
        try:
            file = self.add_file(form.get('file'), properties)
        except XWFFileError, x:
            message = '''<p>There was a problem adding the file: %s</p>''' % x
            return {'message': message, 'error': True}
        
        sendEmailNotification = form.get('sendEmailNotification', 0)
        try:
            sendEmailNotification = int(sendEmailNotification) and True or False
        except ValueError:
            sendEmailNotification = True
        
        if sendEmailNotification:
            self.send_notification(topic=topic, file=file)
        
        message = '''<p>Successfully added the file</p>'''
        
        return {'message': message}
       
    def wf_convertFiletoXWFFile(self, old_file_object):
        """ Convert a regular file object to an XWF file object.
        
        """
        import StringIO
        from Acquisition import aq_get

        f = StringIO.StringIO(old_file_object.data)
        owner = aq_get(old_file_object, '_owner', None, 1)
        
        _file = self.add_file(f)
        _file.manage_changeProperties({'title': old_file_object.getId(),
                                       'dc+Creator': owner[1]})
        _file.changeOwnership(self.acl_users.getUser(owner[1]))
        _file.content_type = old_file_object.content_type
        _file.set_modificationTime(old_file_object.bobobase_modification_time())
        _file.reindex_object()
        
        return 1
        
    def printable_summary(self, result):
        """ Given a result, determine if the summary is actually printable or
        not. If so, return the summary, otherwise return None.
        
        """
        return result.indexable_summary
        
        
    security.declareProtected('Upgrade objects', 'upgrade')
    security.setPermissionDefault('Upgrade objects', ('Manager', 'Owner'))
    def upgrade(self):
        """ Upgrade to the latest version.
            
        """
        currversion = getattr(self, '_version', 0)
        if currversion == self.version:
            return 'already running latest version (%s)' % currversion

        self._version = self.version
        
        return 'upgraded %s to version %s from version %s' % (self.getId(),
                                                              self._version,
                                                              currversion)

Globals.InitializeClass(XWFVirtualFileFolder2)
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
