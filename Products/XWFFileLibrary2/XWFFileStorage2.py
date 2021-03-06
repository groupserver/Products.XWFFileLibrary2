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
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.Folder import Folder
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.XWFCore.XWFUtils import locateDataDirectory
from Products.XWFFileLibrary2.fingerprint import fingerprint_data
import XWFFile2


class XWFFileStorage2(Folder):
    """ The basic implementation for a file storage under XWFFileLibrary.

    """
    security = ClassSecurityInfo()

    meta_type = 'XWF File Storage 2'
    version = 0.9

    base_files_dir = locateDataDirectory("groupserver.XWFFileLibrary2.storage")

    def __init__(self, id):
        """ Initialise a new instance of XWFFileStorage.

            UnitTest: TestXWFFileLibrary
        """
        self.__name__ = id
        self.id = id

    def get_baseFilesDir(self):
        """ """
        return self.base_files_dir

    def add_file(self, data, id_hint=None, force_id=None):
        """ Add a new file to the file storage, returning a reference to the
            file's ID as it was stored.

            Takes raw data. Previously this method required a file object.

        """
        if id_hint and force_id:
            objId = id_hint
        else:
            objId = fingerprint_data(data)

        XWFFile2.manage_addXWFFile2(self, objId, data)
        return objId

    def get_file(self, objId):
        """ Get a file from the file storage, given the file's ID reference.

            UnitTest: TestXWFFileLibrary.test_4_addRemoveFiles
        """
        return getattr(self, objId, None)

    def get_fileIds(self):
        """ Get all the file ids that we currently have in storage.

        Obviously, this should be used sparingly with large numbers of files,
        and the catalog should be used instead.

        """
        return self.objectIds('XWF File 2')

    def remove_file(self, objId):
        """ Remove a file from the file storage, given the file's ID reference.

            UnitTest: TestXWFFileLibrary_test_4_addRemoveFiles
        """
        self.manage_delObjects([objId])

        return 1

    def reindex_storage(self):
        """ Reindex the whole storage.

        """
        for object in self.objectValues('XWF File 2'):
            object.reindex_object()

        return True


# BTreeFolder based storage
class XWFBTreeFileStorage2(BTreeFolder2, XWFFileStorage2):
    meta_type = 'XWF File Storage 2'
    version = 0.9

    def __init__(self, objId):
        BTreeFolder2.__init__(self, objId)
        XWFFileStorage2.__init__(self, objId)

    def populate_storage_from_storage(self, old_storage_id):
        """ Given the ID of another storage, populate this storage.

        """
        old_storage = getattr(self, old_storage_id)
        self._populateFromFolder(old_storage)

InitializeClass(XWFFileStorage2)
InitializeClass(XWFBTreeFileStorage2)

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
    obj = XWFBTreeFileStorage2(id)
    self._setObject(id, obj)

    obj = getattr(self, id)

    if RESPONSE and submit:
        if submit.strip().lower() == 'add':
            RESPONSE.redirect('%s/manage_main' % self.DestinationURL())
        else:
            RESPONSE.redirect('%s/manage_main' % id)


def initialize(context):
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
        icon='icons/ic-filestorage.png')
