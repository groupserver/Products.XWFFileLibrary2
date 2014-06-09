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
from __future__ import absolute_import, division
from datetime import timedelta
from logging import getLogger
log = getLogger('XWFFileLibrary2.XWFVirtualFileFolder2')
import os
from types import *
from AccessControl import getSecurityManager, ClassSecurityInfo
from App.class_init import InitializeClass
#from DateTime import DateTime  # --=mpj17=-- FIXME? datetime.datetime?
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from zope.app.file.image import getImageInfo
from zope.cachedescriptors.property import Lazy
from zope.component import createObject, getMultiAdapter
from zope.interface import implements
from zope.publisher.interfaces import NotFound
# from zope.security.interfaces import Forbidden  # See the fixme below
from gs.core import to_ascii, curr_time as now
from Products.XWFCore.XWFUtils import convertTextToId
from .error import Hidden
from .image import ImageHandler, SquareImageHandler
from .interfaces import IXWFVirtualFileFolder
from .queries import FileQuery
from .requestinfo import RequestInfo
_marker = []


class XWFVirtualFileFolderError(Exception):
    pass


class XWFVirtualFileFolder2(Folder):
    """ A folder for virtualizing file library content.

        When content is 'added' to a 'VirtualFileFolder' the content object
        is cataloged with the appropriate 'virtual_path', and the
        'VirtualFileFolder' knows how to find XWF content that has been placed
        inside itself.

    """
    implements(IXWFVirtualFileFolder)
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

    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w'},
        {'id': 'id_factory', 'type': 'string', 'mode': 'w'},
        {'id': 'xwf_file_library_path', 'type': 'string', 'mode': 'w'},
        {'id': 'ucid', 'type': 'string', 'mode': 'w'},
        {'id': 'public_access_period', 'type': 'int', 'mode': 'w'}
       )

    def __init__(self, folderId, title=None):
        """ Initialise a new instance of XWFVirtualFileFolder.

        """
        super(XWFVirtualFileFolder2, self).__init__(folderId)
        self.__name__ = folderId
        self.title = title if title else folderId
        self.ucid = None

        # period in seconds, defaults to 72 hours
        self.public_access_period = 259200

    @Lazy
    def groupInfo(self):
        retval = createObject('groupserver.GroupInfo', self)
        return retval

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

    def get_xwfFileLibrary(self):
        """ Get the reference to the xwfFileLibrary we are associated with."""
        retval = self.restrictedTraverse(self.xwf_file_library_path)
        return retval

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
        groupInfo = createObject('groupserver.GroupInfo', self)
        query['group_ids'] = [groupInfo.id] if groupInfo else []
        results = library.find_files(query)
        return results

    @Lazy
    def fileQuery(self):
        retval = FileQuery()
        return retval

    security.declarePublic('get_file_by_id')

    def get_file_by_id(self, fileId):
        fid = to_ascii(fileId)
        retval = None
        fileInfo = self.fileQuery.file_info(fid)
        groupInfo = createObject('groupserver.GroupInfo', self)
        if fileInfo is None:
            raise NotFound(self, fid)
        elif fileInfo['group_id'] != groupInfo.id:
            m = u'The file {0} is not in the group {1}'
            raise Unauthorized(m.format(fid, groupInfo.id))
        else:
            l = self.get_xwfFileLibrary()
            s = l.get_fileStorage()
            retval = s.get_file(fid)
        return retval

    security.declarePublic('get_file')

    def get_file(self, REQUEST=None, RESPONSE=None, data_only=False):
        """ """
        if REQUEST.get('REQUEST_METHOD') == 'OPTIONS':
            return self.OPTIONS(REQUEST, RESPONSE)
        elif REQUEST.get('REQUEST_METHOD') == 'PROPFIND':
            return self.PROPFIND(REQUEST, RESPONSE)

        fileId = REQUEST.form.get('id', '')
        fileObject = self.get_file_by_id(fileId)

        if self.fileQuery.file_hidden(fileId):
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
            raise NotFound(self, fileId, REQUEST)
        assert False, 'How did I get here?'

    def get_xsendfile_header(self, REQUEST, RESPONSE):
        sendfile_header = None
        if 'X-Sendfile-Type' in REQUEST:
            sendfile_header = REQUEST.get('X-Sendfile-Type')
        elif 'HTTP_X_SENDFILE_TYPE' in REQUEST:
            sendfile_header = REQUEST.get('HTTP_X_SENDFILE_TYPE')

        return sendfile_header

    def has_public_access(self, fileId):
        retval = False
        fileInfo = self.fileQuery.file_info(fileId)
        if fileInfo:
            p = int(getattr(self, 'public_access_period', 0))
            public_access_period = timedelta(seconds=p)
            retval = now() < (fileInfo['date'] + public_access_period)
        return retval

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
        requestInfo = RequestInfo(REQUEST)
        REQUEST.form['id'] = requestInfo.fileId

        if ((not self.has_public_access(requestInfo.fileId)
            and (not getSecurityManager().checkPermission('View', self)))):
            # FIXME: handle Forbidden errors better
            # m = 'You do not have permission to view the file "{0}"'
            # raise Forbidden(m.format(fileId))
            #
            # For reasons to do with aquisition being awful use the redirector
            # as the came_from
            u = '/login.html?came_from=/r/file/{0}'
            uri = u.format(fileId)
            m = 'Redirecting to <{0}> because there is no public-access for '\
                'the file "{1}"'
            msg = m.format(uri, fileId)
            log.info(msg)
            return self.REQUEST.RESPONSE.redirect(uri)

        try:
            if (requestInfo.isSquare or requestInfo.isResize):
                # we set data_only=True in case the backend uses sendfile
                data = self.get_file(REQUEST, RESPONSE, data_only=True)
            else:
                data = self.get_file(REQUEST, RESPONSE)
        except Hidden as h:  # lint:ok
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
            fid = self.REQUEST.form.get('id', '')
            log.warn("No data found for %s." % fid)
            raise NotFound(self, fid, self.REQUEST)

        if requestInfo.isImageRequest:
            content_type, img_width, img_height = getImageInfo(data)
            img = None
            if (content_type):  # Check to see if we are actually and image
                sendfile_header = self.get_xsendfile_header(REQUEST, RESPONSE)
                if ((requestInfo.width == img_width)
                    and (requestInfo.height == img_height)):
                    log.debug("Not resizing image, existing height and width "
                                 "were the same as requested size")
                elif requestInfo.isResize:
                    handler = ImageHandler(requestInfo.width,
                                            requestInfo.height, sendfile_header)
                    img = handler.get_image_response(data, REQUEST, RESPONSE)
                elif requestInfo.isSquare:
                    handler = SquareImageHandler(requestInfo.squareSize,
                                                    sendfile_header)
                    img = handler.get_image_response(data, REQUEST, RESPONSE)
            data = data if img is None else img
        return data

    security.declareProtected('View', 'hide_file')

    def hide_file(self, fileId):
        """ """
        obj = self.find_files({'id': fileId})[0].getObject()

        tags = list(obj .getProperty('tags', []))
        if 'hidden' not in tags:
            tags.append('hidden')

        obj .manage_changeProperties(tags=tags)
        obj .reindex_object()

        return 'Hidden %s' % fileId

    security.declareProtected('View', 'show_file')

    def show_file(self, fileId):
        """ """
        obj = self.find_files({'id': fileId})[0].getObject()

        tags = list(obj .getProperty('tags', []))
        if 'hidden' in tags:
            tags.remove('hidden')

        obj .manage_changeProperties(tags=tags)
        obj .reindex_object()

        return 'Shown %s' % fileId

    security.declarePublic('OPTIONS')

    def OPTIONS(self, REQUEST, RESPONSE):
        """ Retrieve communication options.

            We disable the publishing of webdav methods.
        """
        self.dav__init(REQUEST, RESPONSE)
        RESPONSE.setHeader('Allow', ', '.join(('GET', 'HEAD', 'POST')))
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
        raise MethodNotAllowed('Method not supported for this resource.')

    def pretty_size(self, size):
        """ Given a size, return a 'prettied' variation that most users will
        understand.

        """
        if size < 5000:
            return 'tiny'
        elif size < 1000000:
            return '{0}KB'.format(size // 1024)
        else:
            return '{0}MB'.format(size // (1024 * 1024))

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


def manage_addXWFVirtualFileFolder2(self, folderId, title='',
                               REQUEST=None, RESPONSE=None, submit=None):
    """ Add a new instance of XWFVirtualFileFolder

    """
    folderId = convertTextToId(folderId)
    title = to_ascii(title) or to_ascii(folderId)
    obj = XWFVirtualFileFolder2(folderId, title)
    self._setObject(folderId, obj)

    obj = getattr(self, folderId)

    if RESPONSE and submit:
        if submit.strip().lower() == 'add':
            RESPONSE.redirect('%s/manage_main' % self.DestinationURL())
        else:
            RESPONSE.redirect('%s/manage_main' % folderId)


def initialize(context):
    context.registerClass(
        XWFVirtualFileFolder2,
        permission='Add XWF Virtual Folder 2',
        constructors=(manage_addXWFVirtualFileFolder2Form,
                      manage_addXWFVirtualFileFolder2),
        icon='icons/ic-virtualfolder.png')
