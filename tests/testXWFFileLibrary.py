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

ZopeTestCase.installProduct('XWFFileLibrary')
ZopeTestCase.installProduct('ZCatalog')
ZopeTestCase.installProduct('ZCTextIndex')
ZopeTestCase.installProduct('XWFIdFactory')
ZopeTestCase.installProduct('XWFCore')

from Products.XWFCore import IXWFXml

testXML = """
<?xml version="1.0" ?>
<root>
  <testnode someattribute="foo">
    Some test text.
  </testnode>
  <emptynode anotherattribute="wibble"/>
</root>"""

testXMLFile = """
<file:file id="1" 
           xmlns:file="http://xwft.org/ns/filelibrary/0.9/"
           xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:Creator>foo_1</dc:Creator>
  <dc:Description>this is a description foo wibble blarg</dc:Description>
  <file:title>1</file:title>
  <dc:Subject>wibble</dc:Subject>
  <dc:Subject>blarg</dc:Subject>
  <dc:Subject>foobar</dc:Subject>
  <dc:Format>application/octet-stream</dc:Format>
  <file:modification_time>2004/10/13 23:49:28.172 GMT+13</file:modification_time>
  <file:id>1</file:id>
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
from Products.XWFIdFactory import XWFIdFactory
class TestXWFFileLibrary(ZopeTestCase.ZopeTestCase):
    def afterSetUp(self):
        self._setupXWFIdFactory()
        filelibrary = self._setupXWFFileLibrary()
        filelibrary.upgrade()
            
        self.filelibrary = filelibrary
        
        self._setupXWFFileStorage('FileStorage1')
        
    def before(self):
        pass
        
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

    def _setupAddFile(self, length):
        """ Add a file of a specific size and return the ID.
        
        """
        f, checksum = createFakeFile(length)
        id = self.filelibrary.FileStorage1.add_file(f)
        
        return id, checksum
        
    def _setupAddFile100(self):
        """ Add 100 files.
        
        """
        for i in xrange(50):
            f, checksum = createFakeFile(100)
            id = self.filelibrary.FileStorage1.add_file(f)
            self.failUnless(self.filelibrary.FileStorage1.get_file(id))
            
            object  = self.filelibrary.FileStorage1.get_file(id)
            
            apply(object.manage_changeProperties, [],
             {'dc+Creator': 'foo_%s' % id,
              'dc+Subject': ['wibble','blarg','foobar'],
              'dc+Description': 'this is a description foo wibble blarg',
             })
        
        for i in xrange(50):
            f, checksum = createFakeFile(100)
            id = self.filelibrary.FileStorage1.add_file(f)
            self.failUnless(self.filelibrary.FileStorage1.get_file(id))
            
            object  = self.filelibrary.FileStorage1.get_file(id)
            
            apply(object.manage_changeProperties, [],
             {'dc+Creator': 'foo_%s' % id,
              'dc+Subject': ['wibble','foo','foobar'],
              'dc+Description': 'this is another description, test one two three',
             })
                                                                                                         
        return 1

    def _searchResults(self, query):
        """ Helper method for getting the results of a query against the
        standard catalog.
        
        """
        return self.filelibrary.Catalog.searchResults(query)

    def _numSearchResults(self, query):
        """ Helper method for getting the number of results from
        a query against the standard catalog.
        
        """
        return len(self._searchResults(query))

    def _assertNumResults(self, query, num):
        """ Helper method for getting the number of results from
        a query against the standard catalog.
        
        """
        self.assertEqual(self._numSearchResults(query), num)


    def _setupTestCatalog(self):
        """ Setup a default catalog for testing.
        
        """
        self._setupAddFile100()
        self._rawCatalog = self.filelibrary.Catalog._catalog
        
    def test_01_fileStorageExists(self):
        self.failUnless(hasattr(self.filelibrary, 'FileStorage1'))

    def test_02_createAdditionalFileStorage(self):
        self._setupXWFFileStorage('FileStorage2')
        # check the new one exists
        self.failUnless(hasattr(self.filelibrary, 'FileStorage2'))
        # check the old one still exists
        self.failUnless(hasattr(self.filelibrary, 'FileStorage1'))

    def test_03_getNextId(self):
        # this should be a brand new namespace, so it should be 1
        self.assertEqual(self.filelibrary.get_nextId(), 1)
        # this should be reusing the same namespace, so it should be 2
        self.assertEqual(self.filelibrary.get_nextId(), 2)

    def test_04_addRemoveFiles(self):
        ids = [('1', 0),('2', 1000),('3',10000),('4', 100000)]
        
        for id, size in ids:
            # try to add the file
            sid, checksum = self._setupAddFile(size)
            self.assertEqual(sid, id)
            
            # try to retrieve the file
            f = self.filelibrary.FileStorage1.get_file(id)
            self.assertNotEqual(f, None)
            
            # check that it is definitely the same file
            self.assertEqual(md5.new(f.read()).hexdigest(), checksum)

        # check that we have accurate ids
        current_ids = self.filelibrary.FileStorage1.get_fileIds()
        ids_only = map(lambda x: x[0], ids)
        for id in current_ids:
            self.failUnless(id in ids_only)
        
        # remove the files
        for id,size in ids:
            self.assertEqual(self.filelibrary.FileStorage1.remove_file(id), 1)
            
        # check that the file metadata has really gone
        for id,size in ids:
            self.failIf(hasattr(self.filelibrary.FileStorage1, id))

    def test_05_checkFileInterfaces(self):
        sid, checksum = self._setupAddFile(1)
        f = self.filelibrary.FileStorage1.get_file(sid)
        self.assertEqual(IXWFXml.IXmlProducer.isImplementedBy(f), 1)

    # various tests against the fields of the catalog
    def test_06_fieldIndexSearch(self):
        self._setupTestCatalog()
        # check that our field index is working
        for i in xrange(1,101):
            for item in self._searchResults({'dc+Creator': 'foo_%s' % i}):
                object = item.getObject()
                self.assertEqual(object.getProperty('dc+Creator', None), 
                                 'foo_%s' % i)
    
    def test_07_dateIndexSearch(self):
        from DateTime import DateTime
        self._setupTestCatalog()
        # check that our date indexes are working
        #
        # we should have exactly 100 files with a modification time earlier
        # than now
        self._assertNumResults(
            {'modification_time': {'query': DateTime()+1, 'range': 'max'}}, 100)
        
        # conversely, we should have exactly 0 files with a modification time
        # later than now
        self._assertNumResults(
            {'modification_time': {'query': DateTime()+1, 'range': 'min'}}, 0)

    def test_08_keywordIndexSearch(self):
        self._setupTestCatalog()

        # check that our keyword indexes are working
        self._assertNumResults({'dc+Subject': 'wibble'},
            100)
        self._assertNumResults({'dc+Subject': 'foo'},
            50)
        self._assertNumResults({'dc+Subject': 'nonexistant'},
            0)
       
    def test_09_textIndexSearch(self):
        self._setupTestCatalog()

        # check that our text indexes are working
        
        # globbing - match
        self._assertNumResults({'dc+Description': 'anot*'}, 50)
        
        # globbing - non match
        self._assertNumResults({'dc+Description': 'decr*'}, 0)
        
        # only half of our objects have both 'description' _and_ 'wibble'
        self._assertNumResults({'dc+Description': 'description and wibble'}, 50)
        
        # as above (the 'and' should be implied)
        self._assertNumResults({'dc+Description': 'description wibble'}, 50)

        # foobar doesn't exist in our descriptions, but the 'or' should still
        # match for 'wibble' and 'another'
        self._assertNumResults(
                       {'dc+Description': 'wibble or foobar or another'}, 100)
        
        # foobar doesn't exist in our descriptions, so the 'and' should fail
        self._assertNumResults({'dc+Description': 'wibble and foobar'}, 0)        
        
        # eliminate 'wibble' from the search set
        self._assertNumResults({'dc+Description': 'description and not wibble'}, 50)
        
        # an alternate form of the above
        self._assertNumResults({'dc+Description': 'description -wibble'}, 50)
         
        # not a test case for a failure, so much as a possible change in semantic
        # I was a _little_ suprised that you couldn't do this, even though you 
        # can do the above, so it would be nice to know if this changes
        from Products.ZCTextIndex import ParseTree
        try:
            self._searchResults({'dc+Description': 'description and -wibble'})
            self.fail('Expected parse error for use of "-" with preceeding "and"')
        except ParseTree.ParseError:
            pass
        
    def test_10_virtualPathIndex(self):
        # we no longer test for this, because support was removed
        return
        self._setupTestCatalog()

        keys = self._rawCatalog.data.keys()
        self.assertEqual(len(keys), 100)
        for key in keys:
            data = self._rawCatalog.getIndex('virtual_path').getEntryForObject(key)
            if not data:
                self.fail('Expected virtual_paths index to have key %s' % key)
        
        for key in self._rawCatalog.getIndex('virtual_path')._unindex.keys():
            if not self._rawCatalog.data.has_key(key):
                self.fail('Expected catalog data to have key %s, since it was '
                          'indexed in virtual_paths' % key)
        
    def test_11_virtualPathIndexSearch(self):
        # we no longer test for this, because support was removed
        return
        self._setupTestCatalog()

        # test our virtual paths indexing
        self._assertNumResults({'virtual_path': '/two/three/'}, 100)
        
        self._assertNumResults({'virtual_path': '/one/two/three/'}, 50)
        
        self._assertNumResults({'virtual_path': 'four'}, 0)
        
        self._assertNumResults({'virtual_path': {'query': 'four', 'level': 2}}, 100)
            
        self._assertNumResults({'virtual_path': {'query': 'four', 'level': 1}}, 50)

    def test_12_findFiles(self):
        self._setupTestCatalog()
        results = map(lambda x: x.id,
                      self.filelibrary.find_files(
                          {'virtual_path': '/one/two/three/',
                           'sort_order': 'descending',
                           'sort_on': 'id'}))
        self.assertEqual(results[:4], ['9','8','7','6'])

    def test_13_fileAsXml(self):
        self._setupTestCatalog()
        f = self.filelibrary.FileStorage1.get_file('1')
        # check that the XML format is what we are expecting, but remove the
        # modification_time first, since that will obviously have changed.
        self.failUnless(minimallyEqualXML(f.get_xml(), testXMLFile, 
                                          ('file:modification_time',)))
        
    def test_14_changeContentType(self):
        self._setupTestCatalog()
        f = self.filelibrary.FileStorage1.get_file('1')
        
        apply(f.manage_changeProperties, (), {'dc+Format': 'application/wibble'})
        self.assertEqual(f.getProperty('dc+Format'), 'application/wibble')
        self.assertEqual(f.content_type, 'application/wibble')

if __name__ == '__main__':
    print framework(descriptions=1, verbosity=1)
else:
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestXWFFileLibrary))
        return suite
