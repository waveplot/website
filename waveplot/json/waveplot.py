#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
import json
import uuid

from flask import request, Response, make_response

from waveplot import app, VERSION
from waveplot.passwords import passwords

import waveplot.image
import waveplot.utils

db_con = db.connect(user=passwords['mysql']['username'], passwd=passwords['mysql']['password'], db='waveplot', use_unicode=True)

CROSS_DOMAIN_ALLOWED = ['http://localhost', 'http://pi.ockmore.net', 'http://waveplot.ockmore.net']

def check_cross_domain(response):
    origin = request.headers.get('Origin',None)
    if origin in CROSS_DOMAIN_ALLOWED:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        print origin

def waveplot_list(value):
    if not db_con.is_connected():
        db_con.reconnect()
    else:
        db_con.commit()

    cur = db_con.cursor()

    page = int(request.args.get('page', "1"))
    limit = int(request.args.get('limit', "20"))

    offset = (page-1)*limit

    query = "SELECT waveplots.uuid, recordings.cached_title, artist_credits.name, waveplots.thumbnail_data FROM waveplots JOIN (recordings,releases,artist_credits) ON (waveplots.recording_mbid=recordings.mbid AND waveplots.release_mbid=releases.mbid AND releases.cached_artist_credit=artist_credits.id) LIMIT %s OFFSET %s"
    data = (limit,offset)
    cur.execute(query,data)

    rows = cur.fetchall()

    results = list({b"uuid":r[0],b'title':r[1],b'artist':r[2],b"data":r[3]} for r in rows)
    for result in results:
        if result[b'title'] == None:
            print result

    response = make_response(json.dumps(results))
    check_cross_domain(response)

    return response


def waveplot_uuid_get(value):

    if not db_con.is_connected():
        db_con.reconnect()

    cur = db_con.cursor()

    information = [
        b'uuid',
        b'length',
        b'trimmed_length',
        b'recording_mbid',
        b'release_mbid',
        b'source',
        b'num_channels',
        b'dr_level',
        b'audio_barcode' ]

    query = b"SELECT " + b','.join(information) + b" FROM waveplots WHERE uuid=%s"
    data = (value,)

    cur.execute(query,data)
    rows = cur.fetchall()

    results = dict(zip(information,rows[0]))
    results['length'] = waveplot.utils.secsToHMS(results['length'].total_seconds())
    results['trimmed_length'] = waveplot.utils.secsToHMS(results['trimmed_length'].total_seconds())
    results['dr_level'] = results['dr_level'] / 10

    results[b'recording']={b'mbid':results[b'recording_mbid']}
    del(results[b'recording_mbid'])

    results[b'release']={b'mbid':results[b'release_mbid']}
    del(results[b'release_mbid'])

    results[b'preview']=open(waveplot.image.waveplot_uuid_to_filename(value)+"_preview",'rb').read()

    response = make_response(json.dumps(results))
    check_cross_domain(response)

    return response

def waveplot_uuid_put(value):
    return 'put'

def waveplot_uuid_delete(value):
    return 'delete'

def waveplot_uuid(value):
    if request.method == b'GET':
        return waveplot_uuid_get(value)
    elif request.method == b'PUT':
        return waveplot_uuid_put(value)
    elif request.method == b'DELETE':
        return waveplot_uuid_delete(value)

    return "mbid"

@app.route('/json/waveplot/<value>', methods=['GET','PUT','DELETE'])
def waveplot_all(value):
    if value.startswith(b'list'):
        return waveplot_list(value)
    else:
        return waveplot_uuid(value)

@app.route('/json/waveplot', methods=['POST'])
def waveplot_post():
    if request.form.get('version', None) != VERSION:
        return json.dumps({u'result':u'failure',u'error':u"Incorrect client version or no version provided."})

    if not db_con.is_connected():
        db_con.reconnect()

    cur = db_con.cursor()

    f = dict((k,v) for (k,v) in request.form.iteritems())

    required_data = [b'recording',b'release',b'track',b'disc',b'image',b'source',
        b'num_channels', b'length', b'trimmed', b'editor', b'dr_level']

    for a in required_data:
        if a not in f:
            return json.dumps({u'result':u'failure',u'error':u"Required data not provided. ({})".format(a.encode('ascii'))})

    f[b'length'] = int(f[b'length'])
    f[b'trimmed'] = int(f[b'trimmed'])

    image = waveplot.image.WavePlotImage(f[b'image'])
    image_hash = image.sha1_hex()

    raw_image_data = image.raw_data

    #Check for existing identical waveplot
    cur.execute("SELECT uuid FROM waveplots WHERE image_hash=%s", (image_hash,))
    rows = cur.fetchall()

    if len(rows) > 0:
        return json.dumps({u'result':u'success',u'uuid':rows[0][0]})

    cur.execute("SELECT id FROM editors WHERE activation_key=%s", (f['editor'],))
    rows = cur.fetchall()

    if len(rows) == 0:
        return json.dumps({u'result':u'failure',u'error':u"Bad editor key ({})".format(f['editor'])})

    editor = rows[0][0]

    generated_uuid = uuid.uuid4()
    cur.execute("SELECT uuid FROM waveplots WHERE uuid='{}'".format(generated_uuid.hex))
    while len(cur.fetchall()) != 0:
        generated_uuid = uuid.uuid4()
        cur.execute("SELECT uuid FROM waveplots WHERE uuid='{}'".format(generated_uuid.hex))

    image.generate_image_data()

    query = "INSERT INTO waveplots \
        (uuid,length,trimmed_length,editor_id,recording_mbid, release_mbid,\
        track,disc,image_hash,source,num_channels,version,dr_level,thumbnail_data) \
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    data = (generated_uuid.hex, waveplot.utils.secsToHMS(f['length']),
        waveplot.utils.secsToHMS(f['trimmed']), editor, f['recording'],
        f['release'], f['track'], f['disc'], image_hash, f['source'],
        f['num_channels'], VERSION, int(float(f['dr_level']) * 10.0),image.b64_thumb)
    cur.execute(query,data)

    cur.execute(u"SELECT waveplot_count FROM recordings WHERE mbid=%s", (f['recording'],))
    rows = cur.fetchall()

    if len(rows) == 0:
        cur.execute(u"INSERT INTO recordings VALUES (%s,%s,%s)", (f['recording'], None, 1))
    else:
        cur.execute(u"UPDATE recordings SET waveplot_count=%s WHERE mbid=%s", (rows[0][0] + 1, f['recording']))

    cur.execute(u"SELECT tracks, dr_level FROM releases WHERE mbid=%s", (f['release'],))
    result = cur.fetchall()

    if len(result) == 0:
        cur.execute(u"INSERT INTO releases (mbid, dr_level) VALUES (%s,%s)", (f['release'], int(float(f['dr_level']) * 10.0)))
    else:
        rel_tracks = result[0][0]
        rel_dr_level = result[0][1]
        rel_dr_level *= rel_tracks
        rel_dr_level += int(float(f['dr_level']) * 10.0)
        rel_tracks += 1
        rel_dr_level /= rel_tracks
        cur.execute(u"UPDATE releases SET dr_level=%s,tracks=%s WHERE mbid=%s", (rel_dr_level, rel_tracks, f['release']))

    db_con.commit()

    image.save(generated_uuid.hex)

    return json.dumps({u'result':u'success',u'uuid':generated_uuid.hex})
