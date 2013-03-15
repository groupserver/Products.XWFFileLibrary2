# -*- coding: utf-8 -*-
from zope.app.file.browser.file import FileView
from gs.content.base import SitePage
from gs.image import GSImage, GSSquareImage
import logging
log = logging.getLogger('XWFFileLibrary2.ImageHandler')


class DisplayFile(FileView, SitePage):
    pass


class ImageHandler(object):

    def __init__(self, width, height, xSendfileHeader):
        self.width = width
        self.height = height
        self.xSendfileHeader = xSendfileHeader

    def get_image_response(self, data, request, response):
        # if we can use sendfile, we use that instead of returning
        # the file through Zope
        retval = None
        origImg = GSImage(data)
        if self.xSendfileHeader:
            log.debug('Using x-sendfile')
            # if we are going to use sendfile, we can either return the cached
            # image, or return the original image, depending on whether we
            # actually resized it
            cache_path = origImg.get_cache_name(self.width, self.height)
            if cache_path:
                response.setHeader(self.xSendfileHeader, cache_path)
                retval = 'image'
        else:
            img = origImg.get_resized(self.width, self.height)
            if img:
                retval = DisplayFile(img, request).show()
        return retval


class SquareImageHandler(object):

    def __init__(self, size, xSendfileHeader):
        self.size = size
        self.xSendfileHeader = xSendfileHeader

    def get_image_response(self, data, request, response):
        # TODO: sendfile
        retval = None
        origImg = GSSquareImage(data)
        if self.xSendfileHeader:
            log.debug('Using x-sendfile')
            # if we are going to use sendfile, we can either return the cached
            # image, or return the original image, depending on whether we
            # actually resized it
            cache_path = origImg.get_cache_name(self.size)
            if cache_path:
                response.setHeader(self.xSendfileHeader, cache_path)
                retval = 'image'
        else:
            img = origImg.get_resized(self.size)
            if img:
                retval = DisplayFile(img, request).show()
        return retval
