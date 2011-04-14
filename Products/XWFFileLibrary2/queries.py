# coding=utf-8
import sqlalchemy as sa
from datetime import datetime
from pytz import UTC

class FileQuery(object):
    def __init__(self, context, da):
        self.context = context
        
        self.postTable = da.createTable('post')
        self.fileTable = da.createTable('file')
        
    def file_hidden(self, fileId):
        pt = self.postTable
        ft = self.fileTable
        s = sa.select([pt.c.hidden])
        s.append_whereclause(ft.c.file_id == fileId)
        s.append_whereclause(pt.c.post_id == ft.c.post_id)
        
        retval = True # A bit harsh
        r = s.execute()
        if r.rowcount == 1:
            row = r.fetchone()
            retval = bool(row['hidden'])
        assert type(retval) == bool
        return retval

