# coding=utf-8
from urlparse import urlparse
from urllib import quote
from zope.cachedescriptors.property import Lazy
from zope.component import createObject
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from gs.errormesg.baseerror import BaseErrorPage
from gs.group.messages.post.hiddendetails import HiddenPostInfo
from queries import FileQuery

class FileHidden(BaseErrorPage):
    index = ZopeTwoPageTemplateFile('browser/templates/posthidden.pt')
    def __init__(self, context, request):
        BaseErrorPage.__init__(self, context, request)
        self.requested = request.form.get('q', '')
        self.fileId = request.form.get('f', '')
        assert self.fileId, 'File ID not set on the file hidden page'

    def quote(self, msg):
        assert msg
        retval = quote(msg)
        assert retval
        return retval

    def __call__(self, *args, **kw):
        contentType = 'text/html; charset=UTF-8'
        self.request.response.setHeader('Content-Type', contentType)
        self.request.response.setStatus(410, lock=True)
        return self.index(self, *args, **kw)

    @Lazy
    def details(self):
        print 'file id %s' % self.fileId
        postId = self.query.postId_from_fileId(self.fileId)
        print 'post Id %s' % postId
        retval = HiddenPostInfo(self.context, postId)
        return retval

    @Lazy
    def query(self):
        da = self.context.zsqlalchemy
        assert da
        retval = FileQuery(self.context, da)
        assert retval
        return retval

