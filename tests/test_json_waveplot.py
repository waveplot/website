#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import mysql.connector as db
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

db_con = db.connect(user=passwords['mysql']['username'], password=passwords['mysql']['password'], database='waveplot_test')

class TestJSONWaveplot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cur = db_con.cursor()
        cur.execute("SHOW TABLES")
        rows = cur.fetchall()

        cls.tables = list(row[0] for row in rows)

        cls.version_error = {u'result':u'failure',u'error':u"Incorrect client version or no version provided."}

        cls.data_error = {u'result':u'failure',u'error':u"Required data not provided."}
        cls.success = {u'result':u'success',u'uuid':''}

        cls.test_image_data = '\x00\x01\x02'

        test_file.db_con = db_con

        cls.test_data = {
            b'version':VERSION,
            b'recording':'d1de259e-4666-4c41-b366-3969c8338ca8',
            b'release':'b5885b2d-afae-47b1-945e-6e1869590974',
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
            b'uuid':'',
            b'audio_barcode': None,
            b'recording': {
                b'mbid':cls.test_data[b'recording']
            },
            b'source': cls.test_data[b'source'],
            b'length': waveplot.utils.secsToHMS(int(cls.test_data[b'length'])),
            b'trimmed_length': waveplot.utils.secsToHMS(int(cls.test_data[b'trimmed'])),
            b'release':{
                b'mbid':cls.test_data[b'release']
            },
            b'num_channels':1,
            b'dr_level':float(int(float(cls.test_data[b'dr_level'])*10))/10
        }

    def setUp(self):
        cur = db_con.cursor()
        for table in self.tables:
            cur.execute("TRUNCATE TABLE {}".format(table))

        db_con.commit()

        cur.execute("INSERT INTO editors (name,email,activated,activation_key) VALUES ('LordSputnik','ben.sput@gmail.com',1,12345)")
        db_con.commit()

    def test_waveplot(self):
        with app.test_request_context('/json/waveplot', method='POST'):

            request.form = {
                b'version':''
            }

            result = json.loads(test_file.waveplot_post())
            self.assertEqual(result,self.version_error)

            request.form[b'version'] = VERSION

            result = json.loads(test_file.waveplot_post())
            self.assertTrue(result[u'error'].startswith(self.data_error[u'error']))

            request.form = self.test_data

            result = json.loads(test_file.waveplot_post())
            self.assertEqual(result[u'result'],u'success')

            uuid = result[u'uuid']

            result = json.loads(test_file.waveplot_post())
            self.assertEqual(result[u'uuid'],uuid)

    def test_waveplot_mbid_get(self):
        #Set up database
        with app.test_request_context('/json/waveplot', method='POST'):

            request.form = self.test_data
            result = json.loads(test_file.waveplot_post())
            self.assertEqual(result[u'result'],u'success')

            self.test_response[b'uuid'] = result[u'uuid'].encode('ascii')

        with app.test_request_context('/json/waveplot/'+result[u'uuid'].encode('ascii'), method='GET'):
            result = json.loads(test_file.waveplot_all(result[u'uuid'].encode('ascii')))

            self.assertEqual(result,self.test_response)


    def test_waveplot_list(self):
        test_results = {}
        with app.test_request_context('/json/waveplot', method='POST'):

            request.form = self.test_data

            for i in xrange(2,32):
                test_data = self.test_image_data[0:2] + chr(i)
                request.form[b'image'] = base64.b64encode(zlib.compress(test_data))
                result = json.loads(test_file.waveplot_post())
                self.assertEqual(result[u'result'],u'success')

                img = waveplot.image.WavePlotImage(request.form[b'image'])

                img._make_thumb_image_()
                test_results[result[u'uuid'].encode('ascii')] = img.b64_thumb



        with app.test_request_context('/json/waveplot/list', method='GET'):
            result = json.loads(test_file.waveplot_list(''))
            self.assertEqual(len(result),20)

            for r in result:
                self.assertEqual(r['data'],test_results[r['uuid']])

            request.args = {'page':'2'}
            result = json.loads(test_file.waveplot_list(''))

            self.assertEqual(len(result),10)

            for r in result:
                self.assertEqual(r['data'],test_results[r['uuid']])


