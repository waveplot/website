#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
import json

from flask import request, make_response

from waveplot import app
from waveplot.passwords import passwords

import waveplot.utils

db_con = db.connect(host = passwords['mysql']['host'], user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot', use_unicode = True, charset = "utf8")

def recording_list():
    cur = waveplot.utils.get_cursor(db_con)

    min_linked_waveplots = int(request.args.get('linked-waveplots', "1"))
    page = int(request.args.get('page', "1"))
    limit = int(request.args.get('limit', "20"))

    offset = (page - 1) * limit

    cur.execute("SELECT mbid, waveplot_count FROM recordings WHERE waveplot_count>=%s ORDER BY waveplot_count DESC LIMIT %s OFFSET %s", (min_linked_waveplots, limit, offset))
    rows = cur.fetchall()

    results = list({u"mbid":r[0], u'count':r[1]} for r in rows)

    response = make_response(json.dumps(results))

    return response

def recording_mbid_get(value):
    cur = waveplot.utils.get_cursor(db_con)

    waveplot_information = [
        b'uuid',
        b'audio_barcode' ]

    query = b"SELECT " + b','.join(waveplot_information) + b" FROM waveplots WHERE recording_mbid=%s"
    data = (value,)

    cur.execute(query, data)
    rows = cur.fetchall()

    results = {b'mbid':value, b'waveplots':[]}

    for row in rows:
        results[b'waveplots'].append(dict(zip(waveplot_information, row)))

    return make_response(json.dumps(results))


def recording_mbid_put(value):
    return 'put'

def recording_mbid(value):
    if request.method == b'GET':
        return recording_mbid_get(value)


@app.route('/json/recording/<value>', methods = ['GET', 'PUT'])
@waveplot.utils.crossdomain(origin = '*')
def recording_all(value):
    if value.startswith("list"):
        return recording_list()
    else:
        return recording_mbid(value)
