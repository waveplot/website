#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
import unittest
import base64
import zlib
import json
import random
import uuid

from waveplot.passwords import passwords
import waveplot.utils
import waveplot.image

import waveplot.json.recording as test_file
import waveplot.json.waveplot

from flask import request

from waveplot import app, VERSION

class TestJSONRecordings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_con = db.connect(host = "localhost", user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot_test', use_unicode = True, charset = "utf8")
        cur = waveplot.utils.get_cursor(cls.db_con)
        cur.execute("SHOW TABLES")
        rows = cur.fetchall()

        cur.close()

        cls.tables = list(row[0] for row in rows)

        cls.test_image_data = '\x00\x01\x02'

        test_file.db_con = cls.db_con
        waveplot.json.waveplot.db_con = cls.db_con

        cls.test_data = {
            b'version':VERSION,
            b'recording':u'',
            b'release':u'b5885b2d-afae-47b1-945e-6e1869590974',
            b'track':'1',
            b'disc':'1',
            b'image':base64.b64encode(zlib.compress(cls.test_image_data)),
            b'source':'flac-0',
            b'num_channels':'1',
            b'length':'143',
            b'trimmed':'140',
            b'editor':'12345',
            b'dr_level':'10.3'
        }

        cls.test_recordings = []

        for i in xrange(0, 30):
            for j in xrange(1, random.randint(2, 5)):
                cls.test_recordings.append(str(uuid.uuid4()))

    def setUp(self):
        cur = self.db_con.cursor()
        for table in self.tables:
            cur.execute("TRUNCATE TABLE {}".format(table))

        self.db_con.commit()

        cur.execute("INSERT INTO editors (name,email,activated,activation_key) VALUES ('LordSputnik','ben.sput@gmail.com',1,12345)")
        self.db_con.commit()

        cur.close()

    def test_recording_list(self):
        test_results = {}
        with app.test_request_context('/json/waveplot', method = 'POST'):

            request.form = self.test_data

            for i in xrange(0, len(self.test_recordings)):
                test_data = self.test_image_data[0:2] + chr(i)
                request.form[b'recording'] = self.test_recordings[i]
                request.form[b'image'] = base64.b64encode(zlib.compress(test_data))
                result = json.loads(waveplot.json.waveplot.waveplot_post().response[0])
                self.assertEqual(result[u'result'], u'success')

                img = waveplot.image.WavePlotImage(request.form[b'image'])

                img._make_thumb_image_()

        with app.test_request_context('/json/recording/list', method = 'GET'):
            result = json.loads(test_file.recording_list().response[0])

            for r in result:
                self.assertEqual(r[u'count'], self.test_recordings.count(r[u'mbid']))

            request.args = {'page':'2'}
            result = json.loads(test_file.recording_list().response[0])

            for r in result:
                self.assertEqual(r[u'count'], self.test_recordings.count(r[u'mbid']))

    def test_recording_mbid(self):
        test_results = {}
        with app.test_request_context('/json/waveplot', method = 'POST'):

            request.form = self.test_data

            for i in xrange(0, len(self.test_recordings)):
                test_data = self.test_image_data[0:2] + chr(i)
                request.form[b'recording'] = self.test_recordings[i]
                request.form[b'image'] = base64.b64encode(zlib.compress(test_data))
                result = json.loads(waveplot.json.waveplot.waveplot_post().response[0])
                self.assertEqual(result[u'result'], u'success')

                img = waveplot.image.WavePlotImage(request.form[b'image'])

                img._make_thumb_image_()

        with app.test_request_context('/json/recording/list', method = 'GET'):
            results = dict()
            for recording in self.test_recordings:
                results[recording] = json.loads(test_file.recording_mbid_get(recording).response[0])

            for k, v in results.iteritems():
                self.assertEqual(k, v[u'mbid'])
                self.assertEqual(self.test_recordings.count(k), len(v[u'waveplots']))
                for w in v[u'waveplots']:
                    self.assertIn("uuid", w)
                    self.assertIn("audio_barcode", w)

    @classmethod
    def tearDownClass(cls):
        cls.db_con.close()
