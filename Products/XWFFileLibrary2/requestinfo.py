# -*- coding: utf-8 -*-


class RequestInfo(object):

    def __init__(self, request):
        self.tsp = request.traverse_subpath

        self.fileId = self.tsp[1]
        # a workaround for an odd bug
        if self.fileId == 'f':
            self.fileId = self.tsp[2]
            self.tsp.pop(1)

    @property
    def isResize(self):
        retval = (len(self.tsp) in (5, 6)) and (self.tsp[2] == 'resize')
        return retval

    @property
    def isSquare(self):
        retval = (len(self.tsp) in (4, 5)) and (self.tsp[2] == 'square')
        return retval

    @property
    def isImageRequest(self):
        retval = self.isResize or self.isSquare
        return retval

    @property
    def resizeSize(self):
        retval = (int(self.tsp[3]), int(self.tsp[4]))
        return retval

    @property
    def size(self):
        retval = int(self.tsp[3])
        return retval

    @property
    def width(self):
        retval = int(self.tsp[3]) if self.isImageRequest else None
        return retval

    @property
    def height(self):
        retval = None
        if self.isImageRequest:
            retval = int(self.tsp[4]) if self.isResize else int(self.tsp[3])
        return retval

    @property
    def squareSize(self):
        retval = int(self.tsp[3]) if self.isSquare else None
        return retval
