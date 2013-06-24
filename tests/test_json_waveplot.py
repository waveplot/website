#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
import json
import unittest
import zlib
import base64

from flask import request

from waveplot import app, VERSION
from waveplot.passwords import passwords
import waveplot.json.waveplot as test_file
import waveplot.utils
import waveplot.image
import waveplot.musicbrainz_lookup

class TestJSONWaveplot(unittest.TestCase):
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

        cls.test_data = {
            b'version':VERSION,
            b'recording':u'f87eb4dd-7e3c-4365-a3c8-f144696f5952',
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

        cls.test_response = {
            u'uuid':'',
            u'audio_barcode': None,
            u'recording': {
                u'mbid':cls.test_data[b'recording']
            },
            u'source': cls.test_data[b'source'],
            u'length': waveplot.utils.secsToHMS(int(cls.test_data[b'length'])),
            u'trimmed_length': waveplot.utils.secsToHMS(int(cls.test_data[b'trimmed'])),
            u'release':{
                u'mbid':cls.test_data[b'release'],
                u'title':u'Past Masters'
            },
            u'title':u'Love Me Do',
            u'num_channels':1,
            u'dr_level':float(int(float(cls.test_data[b'dr_level']) * 10)) / 10,
            u'artist':u'The Beatles',
            u'track':1,
            u'disc':1,
            u'preview':u'AAAA'
        }

    def setUp(self):
        cur = self.db_con.cursor()
        for table in self.tables:
            cur.execute("TRUNCATE TABLE {}".format(table))

        self.db_con.commit()

        cur.execute("INSERT INTO editors (name,email,activated,activation_key) VALUES ('LordSputnik','ben.sput@gmail.com',1,12345)")
        self.db_con.commit()

        cur.close()

    def test_waveplot(self):
        version_error = {u'result':u'failure', u'error':u"Incorrect client version or no version provided."}
        data_error = {u'result':u'failure', u'error':u"Required data not provided."}

        with app.test_request_context('/json/waveplot', method = 'POST'):

            request.form = {
                b'version':''
            }

            result = json.loads(test_file.waveplot_post().response[0])
            self.assertEqual(result, version_error)

            request.form[b'version'] = VERSION

            result = json.loads(test_file.waveplot_post().response[0])
            self.assertTrue(result[u'error'].startswith(data_error[u'error']))

            request.form = self.test_data

            result = json.loads(test_file.waveplot_post().response[0])
            self.assertEqual(result[u'result'], u'success')

            uuid = result[u'uuid']

            result = json.loads(test_file.waveplot_post().response[0])
            self.assertEqual(result[u'uuid'], uuid)

    def test_waveplot_uuid_get(self):
        # Set up database
        unavailable_error = {u'result':u'failure', u'error':u"WavePlot unavailable."}
        with app.test_request_context('/json/waveplot', method = 'POST'):

            request.form = self.test_data
            result = json.loads(test_file.waveplot_post().response[0])
            self.assertEqual(result[u'result'], u'success')

            test_uuid = self.test_response[u'uuid'] = result[u'uuid'].encode('ascii')

        with app.test_request_context('/json/waveplot/' + result[u'uuid'].encode('ascii'), method = 'GET'):

            result = json.loads(test_file.waveplot_all(test_uuid).response[0])

            self.assertEqual(result, unavailable_error)

            thread = waveplot.musicbrainz_lookup.LookupThread()
            thread.db_con = self.db_con
            thread._cache_releases_()
            thread._cache_recordings_()

            result = json.loads(test_file.waveplot_all(test_uuid).response[0])

            self.assertEqual(result[u'result'], u'success')
            self.assertEqual(result[u'waveplot'], self.test_response)

    def tast_waveplot_list(self):
        test_results = {}
        with app.test_request_context('/json/waveplot', method = 'POST'):

            request.form = self.test_data

            for i in xrange(2, 32):
                test_data = self.test_image_data[0:2] + chr(i)
                request.form[b'image'] = base64.b64encode(zlib.compress(test_data))
                result = json.loads(test_file.waveplot_post())
                self.assertEqual(result[u'result'], u'success')

                img = waveplot.image.WavePlotImage(request.form[b'image'])

                img._make_thumb_image_()
                test_results[result[u'uuid']] = img.b64_thumb

        with app.test_request_context('/json/waveplot/list', method = 'GET'):
            result = json.loads(test_file.waveplot_all())
            self.assertEqual(len(result), 20)

            for r in result:
                self.assertEqual(r['data'], test_results[r['uuid']])

            request.args = {'page':'2'}
            result = json.loads(test_file.waveplot_all())

            self.assertEqual(len(result), 10)

            for r in result:
                self.assertEqual(r['data'], test_results[r['uuid']])

    @classmethod
    def tearDownClass(cls):
        cls.db_con.close()
