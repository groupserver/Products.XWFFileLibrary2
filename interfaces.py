from zope.interface import Interface, Attribute

class IXWFFile2(Interface):
    """ A file, capable of writing itself out to disk, and storing 
    metadata in the ZODB
    
    """
    data = Attribute("The file data")
    