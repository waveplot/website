#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import mysql.connector as db
import json

from flask import request

from waveplot import app
from waveplot.passwords import passwords

db_con = db.connect(user=passwords['mysql']['username'], password=passwords['mysql']['password'], database='waveplot')

def recording_list(value):
    return "list"

def recording_mbid_get(value):
    if not db_con.is_connected():
        db_con.reconnect()

    cur = db_con.cursor()

    waveplot_information = [
        b'uuid',
        b'audio_barcode' ]

    query = b"SELECT " + b','.join(waveplot_information) + b" FROM waveplots WHERE recording_mbid=%s"
    data = (value,)

    cur.execute(query,data)
    rows = cur.fetchall()

    results = {b'mbid':value,b'waveplots':[]}

    for row in rows:
        results[b'waveplots'].append(dict(zip(waveplot_information,row)))

    return json.dumps(results)


def recording_mbid_put(value):
    return 'put'

def recording_mbid(value):
    if request.method == b'GET':
        return recording_mbid_get(value)


@app.route('/json/recording/<value>', methods=['GET','PUT'])
def recording_all(value):
    if value.startswith("list"):
        return recording_list(value)
    else:
        return recording_mbid(value)
