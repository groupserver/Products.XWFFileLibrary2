# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright © 2014 OnlineGroups.net and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import sqlalchemy as sa
from gs.database import getTable, getSession


class FileQuery(object):
    def __init__(self, context=None):
        self.postTable = getTable('post')
        self.fileTable = getTable('file')

    def file_hidden(self, fileId):
        pt = self.postTable
        ft = self.fileTable
        s = sa.select([pt.c.hidden])
        s.append_whereclause(ft.c.file_id == fileId)
        s.append_whereclause(pt.c.post_id == ft.c.post_id)

        retval = False  # Old files have no post, so can never be hidden.

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

    def file_info(self, fileId):
        ft = self.fileTable
        pt = self.postTable
        s = sa.select([ft.c.file_id, ft.c.mime_type, ft.c.file_name,
                        pt.c.group_id])
        s.append_whereclause(ft.c.file_id == fileId)
        s.append_whereclause(pt.c.post_id == ft.c.post_id)
        retval = None
        session = getSession()
        r = session.execute(s)
        if r.rowcount > 0:
            row = r.fetchone()
            retval = {'file_id': row['file_id'],
                        'mime_type': row['mime_type'],
                        'name': row['file_name'],
                        'group_id': row['group_id'],
                        'date': row['date']}
        return retval
