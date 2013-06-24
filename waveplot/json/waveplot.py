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

db_con = db.connect(host = "localhost", user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot', use_unicode = True, charset = "utf8")

def waveplot_list():
    cur = waveplot.utils.get_cursor(db_con)

    page = int(request.args.get('page', "1"))
    limit = int(request.args.get('limit', "20"))
    recording = request.args.get('recording', "")

    offset = (page - 1) * limit

    if not recording:
        query = "SELECT waveplots.uuid, recordings.cached_title, artist_credits.name, waveplots.thumbnail_data FROM waveplots JOIN (recordings,releases,artist_credits) ON (waveplots.recording_mbid=recordings.mbid AND waveplots.release_mbid=releases.mbid AND releases.cached_artist_credit=artist_credits.id) ORDER BY waveplots.submit_date DESC LIMIT %s OFFSET %s"
        data = (limit, offset)
    else:
        query = "SELECT waveplots.uuid, recordings.cached_title, artist_credits.name, waveplots.thumbnail_data FROM waveplots JOIN (recordings,releases,artist_credits) ON (waveplots.recording_mbid=recordings.mbid AND waveplots.release_mbid=releases.mbid AND releases.cached_artist_credit=artist_credits.id) WHERE waveplots.recording_mbid=%s ORDER BY waveplots.submit_date DESC LIMIT %s OFFSET %s"
        data = (recording, limit, offset)

    cur.execute(query, data)

    rows = cur.fetchall()

    results = list({b"uuid":r[0], b'title':r[1], b'artist':r[2], b"data":r[3]} for r in rows)

    response = make_response(json.dumps(results))

    return response


def waveplot_uuid_get(value):
    cur = waveplot.utils.get_cursor(db_con)

    db_columns = [
        b'waveplots.uuid',
        b'waveplots.length',
        b'waveplots.trimmed_length',
        b'waveplots.recording_mbid',
        b'waveplots.release_mbid',
        b'waveplots.source',
        b'waveplots.num_channels',
        b'waveplots.dr_level',
        b'waveplots.audio_barcode',
        b'waveplots.track',
        b'waveplots.disc',
        b'recordings.cached_title',
        b'artist_credits.name',
        b'releases.cached_title' ]

    query = b"SELECT " + b','.join(db_columns) + b" FROM waveplots JOIN (recordings,releases,artist_credits) ON (waveplots.recording_mbid=recordings.mbid AND waveplots.release_mbid=releases.mbid AND releases.cached_artist_credit=artist_credits.id) WHERE uuid=%s"
    data = (value,)

    info = [u'uuid', u'length', u'trimmed_length', u'recording_mbid', u'release_mbid', u'source', u'num_channels', u'dr_level', u'audio_barcode', u'track', u'disc', u'title', u'artist', u'release_title']

    cur.execute(query, data)
    rows = cur.fetchall()

    if rows:
        results = {u'result':u'success', u'waveplot':{}}
        temp = results[u'waveplot'] = dict(zip(info, rows[0]))
        temp[u'length'] = waveplot.utils.secsToHMS(temp['length'].total_seconds())
        temp[u'trimmed_length'] = waveplot.utils.secsToHMS(temp['trimmed_length'].total_seconds())
        temp[u'dr_level'] = temp[u'dr_level'] / 10


        temp[u'recording'] = {u'mbid':temp[u'recording_mbid']}
        del temp[u'recording_mbid']

        temp[u'release'] = {u'mbid':temp[u'release_mbid'], u'title':temp[u'release_title']}
        del temp[u'release_mbid']
        del temp[u'release_title']

        temp[u'preview'] = open(waveplot.image.waveplot_uuid_to_filename(value) + "_preview", 'rb').read()

        response = make_response(json.dumps(results))
    else:
        response = make_response(json.dumps({u'result':u'failure', u'error':u"WavePlot unavailable."}))

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

    return "uuid"

@app.route('/json/waveplot/<value>', methods = ['GET', 'PUT', 'DELETE'])
@waveplot.utils.crossdomain(origin = '*')
def waveplot_all(value):
    if value.startswith(b'list'):
        return waveplot_list()
    else:
        return waveplot_uuid(value)

@app.route('/json/waveplot', methods = ['POST'])
@waveplot.utils.crossdomain(origin = '*')
def waveplot_post():
    if request.form.get('version', None) != VERSION:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Incorrect client version or no version provided."}))

    cur = waveplot.utils.get_cursor(db_con)

    f = dict((k, v) for (k, v) in request.form.iteritems())

    required_data = [b'recording', b'release', b'track', b'disc', b'image', b'source',
        b'num_channels', b'length', b'trimmed', b'editor', b'dr_level']

    for a in required_data:
        if a not in f:
            return make_response(json.dumps({u'result':u'failure', u'error':u"Required data not provided. ({})".format(a.encode('ascii'))}))

    f[b'length'] = int(f[b'length'])
    f[b'trimmed'] = int(f[b'trimmed'])

    image = waveplot.image.WavePlotImage(f[b'image'])
    image_hash = image.sha1_hex()

    # Check for existing identical waveplot
    cur.execute("SELECT uuid FROM waveplots WHERE image_hash=%s", (image_hash,))
    rows = cur.fetchall()

    if len(rows) > 0:
        return make_response(json.dumps({u'result':u'success', u'uuid':rows[0][0]}))

    cur.execute("SELECT id FROM editors WHERE activation_key=%s", (f['editor'],))
    rows = cur.fetchall()

    if len(rows) == 0:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Bad editor key ({})".format(f['editor'])}))

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
        f['num_channels'], VERSION, int(float(f['dr_level']) * 10.0), image.b64_thumb)
    cur.execute(query, data)

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

    return make_response(json.dumps({u'result':u'success', u'uuid':generated_uuid.hex}))
