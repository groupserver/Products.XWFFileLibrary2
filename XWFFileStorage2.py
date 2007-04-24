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
import os, time, Globals

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from AccessControl import getSecurityManager, ClassSecurityInfo
from Globals import InitializeClass, PersistentMapping
from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder
from OFS.PropertyManager import PropertyManager

import XWFFile2

import ThreadLock, Globals, md5

from zLOG import LOG, INFO

_thread_lock = ThreadLock.allocate_lock()

class XWFFileStorage2(Folder):
    """ The basic implementation for a file storage under XWFFileLibrary.

    """
    security = ClassSecurityInfo()
    
    meta_type = 'XWF File Storage 2'
    version = 0.9

    base_files_dir = os.path.join(Globals.package_home(globals()),
                                 'files')
                                 
    def __init__(self, id):
        """ Initialise a new instance of XWFFileStorage.
            
            UnitTest: TestXWFFileLibrary
        """
        self.__name__ = id
        self.id = id
    
    def get_baseFilesDir(self):
        return self.base_files_dir
    
    def test_addFile(self):
        """ Test adding a file.
        
        """
        import StringIO
        f = StringIO.StringIO('hello, this is a test')
        return os.path.join(self.base_files_dir, self.add_file(f))
        
    def add_file(self, file_object, id_hint=None, force_id=None):
        """ Add a new file to the file storage, returning a reference to the file's ID as
        it was stored.
        
            Takes a file object, which must support the same methods as the built
            in 'file' object (namely, it must support the 'read' method).
        
            UnitTest: TestXWFFileLibrary.test_4_addRemoveFiles
        """
        if not id_hint and not force_id:
            # get the next unique ID from the File Library container
            incid = str(self.get_nextId())
            isotimestamp = time.strftime('%Y-%m-%dT%H%M%SZ', time.gmtime())
            
            id = '%s-%s' % (incid, isotimestamp)
            
            if id_hint:
                try:
                    id += '-%s' % id_hint.strip().join()
                except:
                    pass
        else:
            id = id_hint
        
        XWFFile2.manage_addXWFFile2(self, id, file_object)
        
        return id
        
    def get_file(self, id):
        """ Get a file from the file storage, given the file's ID reference.
        
            UnitTest: TestXWFFileLibrary.test_4_addRemoveFiles
        """
        return getattr(self, id, None)
    
    def get_fileIds(self):
        """ Get all the file ids that we currently have in storage.
        
        Obviously, this should be used sparingly with large numbers of files, and the
        catalog should be used instead.
        
        """
        return self.objectIds('XWF File 2')
    
    def remove_file(self, id):
        """ Remove a file from the file storage, given the file's ID reference.
        
            UnitTest: TestXWFFileLibrary_test_4_addRemoveFiles
        """
        self.manage_delObjects([id])
        
        return 1
    
    def reindex_storage(self):
        """ Reindex the whole storage.
        
        """
        for object in self.objectValues('XWF File 2'):
            object.reindex_object()
            
        return True
        

Globals.InitializeClass(XWFFileStorage2)

#
# Zope Management Methods
#
manage_addXWFFileStorage2Form = PageTemplateFile(
    'management/manage_addXWFFileStorageForm.zpt',
    globals(), __name__='manage_addXWFFileStorage2Form')

def manage_addXWFFileStorage2(self, id,
                             REQUEST=None, RESPONSE=None, submit=None):
    """ Add a new instance of XWFFileStorage.
        
        UnitTest: TestXWFFileLibrary
    """
    obj = XWFFileStorage2(id)
    self._setObject(id, obj)
    
    obj = getattr(self, id)
    
    if RESPONSE and submit:
        if submit.strip().lower() == 'add':
            RESPONSE.redirect('%s/manage_main' % self.DestinationURL())
        else:
            RESPONSE.redirect('%s/manage_main' % id)

def initialize(context):
    import os
        # make sure the base file storage directory has been created
    try:
        os.makedirs(XWFFileStorage2.base_files_dir, 0770)
    except OSError, x:
        if x.errno == 17:
            pass
        else:
            raise
    context.registerClass(
        XWFFileStorage2,
        permission='Add XWF File Storage 2',
        constructors=(manage_addXWFFileStorage2Form,
                      manage_addXWFFileStorage2),
        icon='icons/ic-filestorage.png'
        )
