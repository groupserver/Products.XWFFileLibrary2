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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from AccessControl import ClassSecurityInfo
from OFS.Folder import Folder

from Products.XWFCore.XWFMetadataProvider import XWFMetadataProvider
from Products.XWFIdFactory.XWFIdFactoryMixin import XWFIdFactoryMixin

import Globals

class XWFFileLibraryError(Exception):
    pass

class Record:
    pass

class XWFFileLibrary2(Folder, XWFMetadataProvider, XWFIdFactoryMixin):
    """ A searchable, self indexing file library.

    """
    security = ClassSecurityInfo()
    
    meta_type = 'XWF File Library 2'
    version = 0.42

    manage_options = Folder.manage_options + \
                     ({'label': 'Configure',
                       'action': 'manage_configure'},)
    
    manage_configure = PageTemplateFile('management/main.zpt',
                                        globals(),
                                        __name__='manage_main')
    
    id_namespace = 'http://iopen.net/namespaces/xwft/filelibrary'
    
    def __init__(self, id, file=None):
        """ Initialise a new instance of XWFFileLibrary.
        
            Unittest: TestXWFFileLibrary
            
        """
        self.__name__ = id
        self.id = id
                
    def get_catalog(self):
        """ Get the catalog associated with this file library.
        
        """
        return self.Catalog

    def get_fileStorage(self, storage_id=None):
        """ Get the storage_id given, or the first storage we have.
        
        """
        storages = self.objectValues('XWF File Storage 2')
        
        if not storage_id and storages:
            return storages[0]
        
        for storage in storages:
            if storage.getId() == storage_id:
                return storage
        
        return None
    
    def find_files(self, query):
        """ Return the catalog 'brains' objects representing the results of
        our query.
        
        """
        catalog = self.get_catalog()
        
        # we use an unrestricted search, because actually, we aren't
        # restricting the results here anyway
        return catalog.unrestrictedSearchResults(query)
    
Globals.InitializeClass(XWFFileLibrary2)
#
# Zope Management Methods
#
manage_addXWFFileLibrary2Form = PageTemplateFile(
    'management/manage_addXWFFileLibraryForm.zpt',
    globals(), __name__='manage_addXWFFileLibrary2Form')

def manage_addXWFFileLibrary2(self, id,
                             REQUEST=None, RESPONSE=None, submit=None):
    """ Add a new instance of XWFFileLibrary2.
        
    """
    obj = XWFFileLibrary2(id)
    self._setObject(id, obj)
    
    obj = getattr(self, id)
    
    if RESPONSE and submit:
        if submit.strip().lower() == 'add':
            RESPONSE.redirect('%s/manage_main' % self.DestinationURL())
        else:
            RESPONSE.redirect('%s/manage_main' % id)

def initialize(context):
    context.registerClass(
        XWFFileLibrary2,
        permission='Add XWF File Library 2',
        constructors=(manage_addXWFFileLibrary2Form,
                      manage_addXWFFileLibrary2),
        icon='icons/ic-filelibrary.png'
        )
