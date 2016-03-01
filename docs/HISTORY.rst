Changelog
=========

8.2.1 (2016-02-29)
------------------

* Making the removal of the file more robust

8.2.0 (2015-10-16)
------------------

* Updating the hidden file page, following the changes to
  `gs.group.messages.post.base`_

.. _gs.group.messages.post.base:
   https://github.com/groupserver/gs.group.messages.post.base


8.1.3 (2015-04-14)
------------------

* Naming the reStructuredText files as such
* Changing the canonical repository to GitHub_
* Moving many utilities to `gs.core`_

.. _GitHub:
   https://github.com/groupserver/Products.XWFFileLibrary2

.. _gs.core: https://github.com/groupserver/gs.core


8.1.2 (2014-06-09)
------------------

* Fixing an error with the file-identifier
* Adding some more logging

8.1.1 (2014-03-24)
------------------

* Ensuring ASCII file identifiers

8.1.0 (2014-02-13)
------------------

* Returning the filename and MIME-type as part of the file information
* Adding to the product metadata

8.0.2 (2013-07-14)
------------------

* Fixing an acquisition issue

8.0.1 (2013-04-03)
------------------

* Fixing a bug

8.0.0 (2013-03-15)
------------------

* Adding a ``get_file_by_id`` method
* Using the new ``RequestInfo`` and ``ImageHandler`` classes
* Cleaning up the code

7.1.1. (2012-10-12)
-------------------

* Removing calls to ``gs.group_object``

7.1.0 (2012-08-07)
------------------

* Adding support for ``infrae.wsgi``

7.0.4 (2012-07-20)
------------------

* Adding a new file finger-printing mechanism
* Removing unused code

7.0.3 (2012-06-20)
------------------

* Dropping the data-adaptor and switching to `gs.database`_

.. _gs.database: https://github.com/groupserver/gs.database

7.0.2 (2011-08-31)
------------------

* Changing the ``public_access_period`` to 72 hours

7.0.1 (2011-05-05)
------------------

* Adding a fix for old files, which lack associated posts that
  can be hidden

7.0.0 (2011-04-21)
------------------

* Allowing a file to be hidden
* Quieting down the logging

6.3.0 (2010-07-09)
------------------

* Supporting Zope 2.12+
* Removing the ``send_notification`` and ``cb_file_addFile``
  methods
* Removing unused locking

6.2.0 (2010-03-19)
------------------

* Switching to Mercurial for version control
* Handling ``None`` being returned from ``GSImage.get_resized``

6.1.0 (2009-10-18)
------------------

* Adding support for Apache ``mod_xsendfile``
* Adding auto-versioning

6.0.0 (2009-10-03)
------------------

* Rearranging the product into egg-form

5.1.3 (2009-08-21)
------------------

* Adding a Subversion ``ignore`` file

5.1.2 (2009-07-27)
------------------

* Removing forbidden characters from the file-name

5.1.1 (2009-05-15)
------------------

* Using a new image
* Fixing the constant setting of properties

5.1.0 (2008-09-12)
------------------

* Adding a file-shower from Zope 3

5.0.0 (2008-08-29)
------------------

* Adding the ability to re-size images
* Switching to the ``Products.XWFFileLibrary2`` name-space

4.0.2 (2008-07-01)
------------------

* Adding performance improvements
* Fixing a memory leak

4.0.1 (2008-04-19)
------------------

* Adding a more robust mechanism for passing around the storage
  path

4.0.0 (2007-02-19)
------------------

* Removing the pages from the *Files* area, as this is now
  handled by `gs.group.messages.files`_

.. _gs.group.messages.files:
   https://github.com/groupserver/gs.group.messages.files

3.2.2 (2007-10-17)
------------------

* Removing logging

3.2.1 (2007-10-08)
------------------

* Removing ``manage_configure``

3.2.0 (2007-08-30)
------------------

* Adding support for ``BTree`` based file-storage

3.1.0 (2007-08-21)
------------------

* Added an interface for ``VirtualFileFolder``
* Implemented a public-access period for files

3.0.0 (2007-08-10)
------------------

* Switching to a CSS-sprite based system for the file icons

2.4.0 (2007-07-16)
------------------

* Adding an icon for ``image/x-png`` (thank you Microsoft
  Internet Explorer 7)

2.3.0 (2007-07-08)
------------------

* Adding icons for TIFF images, ``text/enriched``, TeX, and BibTeX

2.2.0 (2007-04-25)
------------------

* Adding a nice 404 message
* Adding icons for Lotus Wordpro, compressed files, and some
  weird Microsoft Excel MIME-types
* Allowing metadata to be added without breaking an existing file

2.1.0 (2007-02-28)
------------------

* Adding icons for CSS files ``pjpeg`` and ``ms-tnef`` files

2.0.0 (2007-02-07)
------------------

* Moving the pane-loader to GSContent_ for resuse

.. _GSContent: https://github.com/groupserver/Products.GSContent

1.10.0 (2006-11-07)
-------------------

* Adding an interface for viewing files
* Adding file-icons as a resource directory

1.9.2 (2006-10-23)
------------------

* Improving the performance by only reading when returning data

1.9.1 (2006-10-19)
------------------

* Fixing some bugs

1.9.0 (2006-09-29)
------------------

* Adding virus scanning

1.8.0 (2006-06-20)
------------------

* Fixing some download issues by allowing the name of file to be
  the URL

1.7.0 (2006-05-22)
------------------

* Adding a method to re-index a file

1.6.0 (2006-05-17)
------------------

* Allowing the notification for a posted file to be suppressed

1.5.0 (2006-04-18)
------------------

* Adding support for hiding files
* Suppressing empty tags
* Filtering files by topic

1.4.1 (2006-03-30)
------------------

* Adding an icon

1.4.0 (2006-03-22)
------------------

* Adding support for copying files
* Sorting by mail-date before the subject
* Fixing a security hole

1.3.0 (2006-03-07)
------------------

* Adding support for removing files

1.2.0 (2006-02-24)
------------------

* Adding summaries
* Stripping path-names (so it just has the file-name)
* Changing the pretty sizes

1.1.0 (2006-02-11)
------------------

* Adding tagging of files

1.0.0 (2006-02-06)
------------------

Initial version. Prior to the creation of this product there were
no files in GroupServer.

..  LocalWords:  Changelog reStructuredText GitHub
