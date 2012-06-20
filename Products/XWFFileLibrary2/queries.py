# coding=utf-8
import sqlalchemy as sa
from datetime import datetime
from pytz import UTC
from gs.database import getTable, getSession

class FileQuery(object):
    def __init__(self, context):
        self.context = context
        self.postTable = getTable('post')
        self.fileTable = getTable('file')
        
    def file_hidden(self, fileId):
        pt = self.postTable
        ft = self.fileTable
        s = sa.select([pt.c.hidden])
        s.append_whereclause(ft.c.file_id == fileId)
        s.append_whereclause(pt.c.post_id == ft.c.post_id)
        
        retval = False # Old files have no post, so can never be hidden.

        session = getSession()
        r = session.execute(s)
        if r.rowcount == 1:
            row = r.fetchone()
            retval = bool(row['hidden'])
        assert type(retval) == bool
        return retval

    def postId_from_fileId(self, fileId):
        pt = self.postTable
        ft = self.fileTable
        s = sa.select([pt.c.post_id])
        s.append_whereclause(ft.c.file_id == fileId)
        s.append_whereclause(pt.c.post_id == ft.c.post_id)
        
        retval = None

        session = getSession()
        r = session.execute(s)
        if r.rowcount == 1:
            row = r.fetchone()
            retval = row['post_id']
        return retval

