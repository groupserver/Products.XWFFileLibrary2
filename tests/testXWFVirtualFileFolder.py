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
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Interface.Implements import implements
from Interface.Exceptions import DoesNotImplement, BrokenImplementation
from Interface.Exceptions import BrokenMethodImplementation

from AccessControl import getSecurityManager

ZopeTestCase.installProduct('XWFFileLibrary')
ZopeTestCase.installProduct('ZCatalog')
ZopeTestCase.installProduct('ZCTextIndex')
ZopeTestCase.installProduct('XWFIdFactory')
ZopeTestCase.installProduct('XWFCore')

from Products.XWFCore import IXWFXml
from Products.XWFCore import XWFUtils

testXML = """
<file:file rdf:id="42" 
xmlns:file="http://xwft.org/ns/filelibrary/0.9/" 
xmlns:dc="http://purl.org/dc/elements/1.1/" 
xmlns:tal="http://xml.zope.org/namespaces/tal" 
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<dc:Creator>testUser_1_</dc:Creator>
<dc:Description>this is a description foo wibble blarg</dc:Description>
<file:modification_time>2003/08/22 17:39:47.205 GMT+12</file:modification_time>
<dc:Subject>wibble</dc:Subject>
<file:title>42</file:title>
<dc:Format>application/octet-stream</dc:Format>
<file:content_folder_id>2</file:content_folder_id>
<file:id>42</file:id>
<file:size>100</file:size>
</file:file>
"""

import StringIO, random, md5
def createFakeFile(length):
    data = []
    for i in xrange(length):
        data.append(chr(random.randrange(1, 255)))
    data = ''.join(data)
    checksum = md5.new(data).hexdigest()
    return StringIO.StringIO(data), checksum

class FakePOSTRequest:
    """ A really minimal class to fake a POST. Probably looks
    nothing like the real thing, but close enough for our needs :)
    
    """
    import StringIO
    stdin = StringIO.StringIO(testXML)

def minimallyEqualXML(one, two, removeElements=()):
    """ Strip all the whitespace out of two pieces of XML code, having first converted
    them to a DOM as a minimal test of equivalence.
    
    """
    from xml.dom import minidom
    
    sf = lambda x: ''.join(filter(lambda y: y.strip(), x))
    
    onedom = minidom.parseString(one)
    twodom = minidom.parseString(two)

    # a hugely hackish way to remove the elements, not full proof, but being
    # a test situation, we should be providing very controlled input
    for element in removeElements:
        oneremovenodes = onedom.getElementsByTagName(element)
        tworemovenodes = twodom.getElementsByTagName(element)
        for removenode in oneremovenodes:
            removenode.parentNode.removeChild(removenode)
        for removenode in tworemovenodes:
            removenode.parentNode.removeChild(removenode)
    
    return sf(onedom.toxml()) == sf(twodom.toxml())

from Products.XWFFileLibrary import XWFFileLibrary
from Products.XWFFileLibrary import XWFFileStorage
from Products.XWFFileLibrary import XWFVirtualFileFolder

from Products.XWFIdFactory import XWFIdFactory
class TestXWFVirtualFileFolder(ZopeTestCase.ZopeTestCase):
    def afterSetUp(self):
        self._setupXWFIdFactory()
        filelibrary = self._setupXWFFileLibrary()
        filelibrary.upgrade()
            
        self.filelibrary = filelibrary
        
        self._setupXWFFileStorage('FileStorage1')
        
        self.virtualff = self._setupXWFVirtualFileFolder(self.folder)
    
    def before(self):
        pass
        
    def _setupXWFVirtualFileFolder(self, container, id='VirtualFileFolder'):
        """ Create a new VirtualFileFolder.
        
        """
        XWFVirtualFileFolder.manage_addXWFVirtualFileFolder(container, id)
        xwfVirtualFileFolder = getattr(container,id)
        xwfVirtualFileFolder.manage_changeProperties(
                            xwf_file_library_path=self.filelibrary.getPhysicalPath())
            
        return getattr(container, id)

    def _setupXWFFileLibrary(self):
        """ Create a new XWFFileLibrary as the basis for our tests.
        
        """
        XWFFileLibrary.manage_addXWFFileLibrary(self.folder, 'FileLibrary')
        
        return self.folder.FileLibrary

    def _setupXWFFileStorage(self, filestorageid):
        """ Create a new XWFFileStorage.
            
        """
        XWFFileStorage.manage_addXWFFileStorage(self.filelibrary, filestorageid)
            
        return 1
        
    def _setupXWFIdFactory(self):
        """ Create a new XWFIdFactory as the basis for our tests.
        
        """
        XWFIdFactory.manage_addXWFIdFactory(self.folder, 'IdFactory', None)
        
        return 1

    def _setupNestedVirtualFileFolders(self, container, level=0, maxlevel=4,
                                             width=2, num_files=3):
        if level >= maxlevel:
            return
            
        for id in xrange(1, width+1):
            nid = 'VirtualFileFolder_%s_%s' % (level, id)
            self._setupXWFVirtualFileFolder(container, nid)
            self._setupNestedVirtualFileFolders(getattr(container, nid), level+1)
            if num_files:
                self._setupAddFiles(container, num_files)
                
    def _setupAddFile(self, length):
        """ Add a file of a specific size and return the ID.
        
        """
        f, checksum = createFakeFile(length)
        _file = self.virtualff.add_file(f)
        
        return _file, checksum
        
    def _setupAddFiles(self, container, num):
        """ Add num files.
        
        """        
        user = getSecurityManager().getUser()
        
        subjectKeywords = ['foo','foobar','wibble','blarg','zeus']

        for i in xrange(num):
            f, checksum = createFakeFile(100)
            object = container.add_file(f)
            
            apply(object.manage_changeProperties, [],
             {'dc+Creator': str(user),
              'dc+Subject': subjectKeywords[i%len(subjectKeywords)],
              'dc+Description': 'this is a description foo wibble blarg',
             })
                                                                     
        return 1
    
    def test_01_createVirtualFileFolder(self):
        # should have been created as part of the test harness
        self.failUnless(self.virtualff)

    def test_02_addSingleFile(self):
        # add a single 100 byte file
        _file, checksum1 = self._setupAddFile(100)
        checksum2 = md5.new(
                  self.virtualff.find_files()[0].getObject().read()).hexdigest()
        self.assertEqual(checksum2, checksum1)

    def test_03_addMultipleFiles(self):
        self._setupAddFiles(self.virtualff, 20)
            
    def test_04_createNestedVirtualFileFolders(self):
        self._setupNestedVirtualFileFolders(self.virtualff)
        
        folders0 = self.virtualff.get_virtualFileFolders(0)
        self.assertEqual(len(folders0), 2)        
         
        folders1 = self.virtualff.get_virtualFileFolders(1)
        self.assertEqual(len(folders1), 6)
        
        folders2 = self.virtualff.get_virtualFileFolders(2)
        self.assertEqual(len(folders2), 14)
        
    def test_05_getFileListing(self):
        self._setupNestedVirtualFileFolders(self.virtualff)
        
        files0 = self.virtualff.find_files()
        files1 = self.virtualff.find_files(recursion_level=1)
        files2 = self.virtualff.find_files(recursion_level=2)
        filesAll = self.virtualff.find_files(recursion_level=-1)
        
        self.assertEqual(len(files0), 6)
        self.assertEqual(len(files1), 18)
        self.assertEqual(len(files2), 42)
        self.assertEqual(len(filesAll), 90)

    def test_06_getQueriedFileListing(self):
        self._setupNestedVirtualFileFolders(self.virtualff)
        
        filesAll = self.virtualff.find_files(recursion_level=-1)
        
        self.assertEqual(len(filesAll), 90)
        
        filesSearched = self.virtualff.find_files(query={'dc+Subject': 'foobar'},
                                                  recursion_level=-1)
        
        # we should only retrieve a fraction of the original fileset
        self.assertEqual(len(filesSearched), 30)
        
    def test_07_convertResultsToXml(self):
        self._setupNestedVirtualFileFolders(self.virtualff)
        
        filesAll = self.virtualff.find_files(recursion_level=-1)

        xmlResult = XWFUtils.convertCatalogResultsToXml((filesAll[11],))
        print xmlResult
        self.failUnless(minimallyEqualXML(xmlResult, testXML, 
                                         ('file:modification_time',)))
      
    def test_08_ucidIsString(self):
        self.assertEqual(type(self.virtualff.ucid), type(''))
        
if __name__ == '__main__':
    print framework(descriptions=1, verbosity=1)
else:
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestXWFVirtualFileFolder))
        return suite
