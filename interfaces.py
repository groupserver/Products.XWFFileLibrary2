from zope.interface import Interface, Attribute

class IXWFFile2(Interface):
    """ A file, capable of writing itself out to disk, and storing 
    metadata in the ZODB
    
    """
    data = Attribute("The file data")
    
class IGSFileInfo(Interface):
    """Information about a particular file in GroupServer"""
    
    def get_id(self):
        """Get the ID of the file.
        
        RETURNS
            A string representing the ID of the file.
            
        SIDE EFFECTS
            None.
        """
        pass
        
    def get_name(self):
        """Get the name of the file.
        
        RETURNS
            A string representing the name of the file.
            
        SIDE EFFECTS
            None.
        """
        pass
    
    def get_mime_type(self):
        """Get the MIME-type of the file.
        
        RETURNS
            A string representing the MIME-type of the file.
            
        SIDE EFFECTS
            None.
        """
        pass
        
    def get_mime_type_image(self):
        """Get the image that represents the MIME-type of the file.
        
        The image that represents the MIME-type of the file is used
        as an icon when displaying the file medatadata. The URL that
        is returned may or may not exist.
        
        RETURNS
            A string representing URL that should point to the image
            that represents the MIME-type of the file.
            
        SIDE EFFECTS
            None.
        """
        pass
        
    def get_short_url(self):
        """Get the short version of the file URL.
        
        There are two versions of the URL that is used to retrieve a file.
        The short version is used when the user will actually see the URL,
        such as in the body of a message, but it goes through a redirector.
        
        RETURNS
            A string representing the short URL.
            
        SIDE EFFECTS
            None.
            
        SEE ALSO
            "self.get_full_url()"
        """
        pass
    
    def get_full_url(self):
        """Get the full URL of the file, that does not use a redirector.
        
        There are two versions of the URL that is used to retrieve a file.
        The full version is used when the user clicks on a link, rather than
        looking directly at the URL. The full URL retrieves the file 
        directly, and does not go through a redirector.
        
        RETURNS
            A string representing the full URL.
        
        SIDE EFFECTS
            None.
            
        SEE ALSO
            "self.get_short_url()"
        """
        pass
            
    def get_size(self):
        """Gets the size of the file in a human-readable form
        
        RETURNS
            A string containing the size of the file, and the measurement
            units.
        
        SIDE EFFECTS
            None.
        """
        pass
