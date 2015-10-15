# -*- coding: utf-8 -*-
############################################################################
#
# Copyright © 2012, 2013, 2014, 2015 OnlineGroups.net and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
############################################################################
from __future__ import absolute_import, unicode_literals, print_function
from gs.core import mailto
from zope.cachedescriptors.property import Lazy
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from gs.errormesg.baseerror import BaseErrorPage
from gs.group.messages.post.hide.hiddendetails import HiddenPostInfo
from .queries import FileQuery


class FileHidden(BaseErrorPage):
    index = ZopeTwoPageTemplateFile(b'browser/templates/posthidden.pt')

    def __init__(self, context, request):
        BaseErrorPage.__init__(self, context, request)
        self.requested = request.form.get('q', '')
        self.fileId = request.form.get('f', '')
        assert self.fileId, 'File ID not set on the file hidden page'

    def __call__(self, *args, **kw):
        contentType = b'text/html; charset=UTF-8'
        self.request.response.setHeader(b'Content-Type', contentType)
        self.request.response.setStatus(410)
        return self.index(self, *args, **kw)

    @Lazy
    def details(self):
        postId = self.query.postId_from_fileId(self.fileId)
        retval = HiddenPostInfo(self.context, postId)
        return retval

    @Lazy
    def query(self):
        retval = FileQuery(self.context)
        assert retval
        return retval

    @Lazy
    def email(self):
        subject = 'Hidden file'
        b = '''Hello,

I wanted to see the file
  <{0}>.
However, it is hidden. I think I should be allowed to see the file
because...'''
        body = b.format(self.requested)
        retval = mailto(self.siteInfo.get_support_email(), subject, body)
        return retval
