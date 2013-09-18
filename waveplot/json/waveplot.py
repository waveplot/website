# -*- coding: utf8 -*-

# Copyright 2013 Ben Ockmore

# This file is part of WavePlot Server.

# WavePlot Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# WavePlot Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with WavePlot Server. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, absolute_import, division

import json
import datetime

from flask import request, make_response


import waveplot.schema
import waveplot.utils

from waveplot import app, VERSION
from waveplot.schema import Session, WavePlot, Track, Recording, Editor

@app.route('/json/waveplot/<value>', methods = ['GET', 'PUT', 'DELETE'])
@waveplot.utils.crossdomain(origin = '*')
def waveplot_all(value):
    if value.startswith('list'):
        return waveplot_list()
    else:
        return waveplot_uuid(value)

def waveplot_list():
    page = int(request.args.get('page', "1"))
    limit = int(request.args.get('limit', "20"))

    offset = (page - 1) * limit

    session = Session()

    if 'recording' in request.args:
        recording = session.query(Recording).filter_by(mbid=request.args['recording']).first()

        if recording is None:
            return make_response(json.dumps({u'result':u'failure', u'error':u"Recording not in database."}))

        waveplots = recording.waveplots
    else:
        waveplots = session.query(WavePlot).order_by(WavePlot.submit_date.desc()).offset(offset).limit(limit)

    results = [{u"uuid":w.uuid, u'title':w.track.title, u'artist':w.track.recording.artist_credit.name, b"data":w.thumbnail_bin} for w in waveplots]

    return make_response(json.dumps(results))

@app.route('/json/waveplot', methods = ['POST'])
@waveplot.utils.crossdomain(origin = '*')
def waveplot_post():
    if request.form.get('version', None) != VERSION:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Incorrect client version or no version provided."}))

    session = Session()

    wp = WavePlot()
    wp.version = VERSION
    wp.submit_date = datetime.datetime.utcnow()

    f = request.form.to_dict()

    required_data = ['recording', 'release', 'track', 'disc', 'image', 'source',
        'num_channels', 'length', 'trimmed', 'editor', 'dr_level']

    l = [a for a in required_data if a not in f]
    if l:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Required data not provided. ({})".format(",".join(l))}))

    wp.length = datetime.timedelta(seconds=int(f['length']))
    wp.trimmed_length = datetime.timedelta(seconds=int(f['trimmed']))

    image = waveplot.image.WavePlotImage(f['image'])

    wp.image_sha1 = image.sha1

    # Check for existing identical waveplot
    if not session.query(WavePlot).filter_by(image_sha1 = image.sha1).count():
        return make_response(json.dumps({u'result':u'success', u'uuid':rows[0][0]}))

    editor = session.query(Editor).filter_by(key=f['editor']).first()
    if editor is None:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Bad editor key ({})".format(f['editor'])}))

    wp.editor_id = editor.id

    generated_uuid = uuid.uuid4()
    while session.query(WavePlot).filter_by(uuid = generated_uuid).count():
        generated_uuid = uuid.uuid4()

    image.generate_image_data()

    wp.thumbnail_bin = image.thumb_data

    wp.num_channels = int(f['num_channels'])
    wp.dr_level = int(float(f['dr_level']) * 10)

    recording = session.query(Recording).filter_by(mbid=f['recording']).first()
    if recording is None:
        recording = Recording(f['recording'])

    recording.waveplot_count += 1
    wp.recording = recording

    # Put track in here with false mbid, until it gets looked up later
    # This is necessary because (afaik) there's no track mbid support in Picard
    generated_mbid = uuid.uuid4()
    while session.query(Track).filter_by(mbid = generated_mbid).count():
        generated_mbid = uuid.uuid4()

    track = Track(generated_mbid, int(f['track']), int(f['disc']), f['release'], f['recording'])
    wp.track = track

    ### STUFF TO FIX ###
    source_type = Column(String(20, collation='ascii_bin'))
    sample_rate = Column(Integer)
    bit_depth = Column(SmallInteger)
    bit_rate = Column(Integer)
    audio_barcode = Column(SmallInteger)

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
