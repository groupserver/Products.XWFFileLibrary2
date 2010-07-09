# Copyright IOPEN Technologies Ltd., 2003
# richard@iopen.net
#
# For details of the license, please see LICENSE.
#
# You MUST follow the rules in http://iopen.net/STYLE before checking in code
# to the head. Code which does not follow the rules will be rejected.  
#

from zope.component import adapter, provideHandler
from interfaces import IXWFFile2
from XWFFile2 import addedFile, movedFile

# import IObjectAddedEvent
try:
  # For Zope 2.13
  from zope.lifecycleevent.interfaces import IObjectAddedEvent
except:
  # For Zope 2.10
  from zope.app.container.interfaces import IObjectAddedEvent

@adapter(IXWFFile2, IObjectAddedEvent)
def added_handler(fileInstance, event):
    addedFile(fileInstance, event)
provideHandler(added_handler)

# import IObjectMovedEvent
try:
  # For Zope 2.13
  from zope.lifecycleevent.interfaces import IObjectMovedEvent
except:
  # For Zope 2.10
  from zope.app.container.interfaces import IObjectMovedEvent
  
@adapter(IXWFFile2, IObjectMovedEvent)
def moved_handler(fileInstance, event):
    movedFile(fileInstance, event)
provideHandler(moved_handler)


def initialize(context):
    # Import lazily, and defer initialization to the module
    import XWFFileLibrary2, XWFFileStorage2, XWFVirtualFileFolder2, XWFFile2
    
    XWFFileLibrary2.initialize(context)
    XWFFileStorage2.initialize(context)
    XWFVirtualFileFolder2.initialize(context)
    XWFFile2.initialize(context)

