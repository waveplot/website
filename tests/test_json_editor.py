#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
import unittest
import json

from flask import request

from waveplot.passwords import passwords
import waveplot.json.editor as test_file

from waveplot import app

import waveplot.utils

class TestJSONEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_con = db.connect(host = "localhost", user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot_test', use_unicode = True, charset = "utf8")
        cur = waveplot.utils.get_cursor(cls.db_con)
        cur.execute("SHOW TABLES")
        rows = cur.fetchall()

        cur.close()

        cls.tables = list(row[0] for row in rows)

        test_file.db_con = cls.db_con

    def setUp(self):
        cur = self.db_con.cursor()
        for table in self.tables:
            cur.execute("TRUNCATE TABLE {}".format(table))

        self.db_con.commit()
        cur.close()

    def test_editor_create(self):
        with app.test_request_context('/json/editor', method = 'POST'):

            request.form = {
                b'username':u'APerson',
                b'email':u'an.email@blob.com'
            }

            result = json.loads(test_file.editor_all().response[0])
            self.assertEqual(result.get(u'result', ''), u'success')

            result = json.loads(test_file.editor_all().response[0])
            self.assertEqual(result.get(u'result', ''), u'failure')
            self.assertEqual(result.get(u'error', ''), u"Email address already registered. Please await your activation email.")

            request.form = {
                b'username':u'APerson',
                b'email':u'an.elblob.com'
            }

            result = json.loads(test_file.editor_all().response[0])
            self.assertEqual(result.get(u'result', ''), u'failure')
            self.assertEqual(result.get(u'error', ''), u"Email address invalid.")

            request.form = {
                b'username':u'',
                b'email':u'another.email@blob.com'
            }

            result = json.loads(test_file.editor_all().response[0])
            self.assertEqual(result.get(u'result', ''), u'failure')
            self.assertEqual(result.get(u'error', ''), u"Missing data. Username and email required.")

            request.form = {
                b'username':u'APerson',
                b'email':u''
            }

            result = json.loads(test_file.editor_all().response[0])
            self.assertEqual(result.get(u'result', ''), u'failure')
            self.assertEqual(result.get(u'error', ''), u"Missing data. Username and email required.")

    @classmethod
    def tearDownClass(cls):
        cls.db_con.close()
