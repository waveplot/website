#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import

import unittest
import mysql.connector as db

if __name__ == '__main__':
    from waveplot.passwords import passwords
    db_con = db.connect(user=passwords['mysql']['username'], password=passwords['mysql']['password'], database='waveplot')

    cur = db_con.cursor()
    cur.execute("SHOW TABLES")
    rows = cur.fetchall()

    db_con.database = 'waveplot_test'

    for table in (row[0] for row in rows):
        cur.execute("DROP TABLE IF EXISTS {}".format(table))

    for table in (row[0] for row in rows):
        cur.execute("CREATE TABLE {} LIKE waveplot.{}".format(table,table))

    db_con.commit()

    suite = unittest.defaultTestLoader.discover("tests")
    unittest.TextTestRunner(verbosity=2).run(suite)