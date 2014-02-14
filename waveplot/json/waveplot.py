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
import uuid
import os.path
import base64

from flask import request, make_response

import waveplot.schema
import waveplot.utils
import waveplot.image

from waveplot import app, VERSION
from waveplot.schema import Session, WavePlot, Track, Recording, Editor, WavePlotContext, Release, uuid_h2b, uuid_b2h

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
    barcode = int(request.args['barcode']) if 'barcode' in request.args else None

    offset = (page - 1) * limit

    session = Session()

    if 'recording' in request.args:
        recording = session.query(Recording).filter_by(mbid=request.args['recording']).first()

        if recording is None:
            return make_response(json.dumps({u'result':u'failure', u'error':u"Recording not in database."}))

        waveplots = recording.waveplots
    else:
        waveplots = session.query(WavePlot)
        if barcode is not None:
            waveplots = waveplots.filter_by(sonic_hash = barcode)

        waveplots = waveplots.order_by(WavePlot.uuid_bin.asc()).offset(offset).limit(limit)

    results = [{
                u"uuid":w.uuid,
                u'title':w.track.title if w.track is not None else None,
                u'artist':w.track.recording.artist_credit.name if w.track is not None else None,
                b"data":base64.b64encode(w.thumbnail_bin)
               } for w in waveplots]

    session.close()

    return make_response(json.dumps(results))

def waveplot_uuid(value):

    session = Session()

    wp = session.query(WavePlot).filter_by(uuid_bin=uuid_h2b(value)).first()

    if wp is None:
        response = make_response(json.dumps({u'result':u'failure', u'error':u"No such WavePlot."}))

    track = wp.track
    release = (track.release if track is not None else None)

    path = waveplot.image.waveplot_uuid_to_filename(value.replace('-', '')) + "_preview"
    if not os.path.exists(path):
        response = make_response(json.dumps({u'result':u'failure', u'error':u"Cannot locate WavePlot preview image."}))

    f = open(path, 'rb')
    preview = base64.b64encode(f.read())

    results = {
        u'result':u'success',
        u'waveplot':{
            u'uuid':wp.uuid,
            u'length':str(wp.length),
            u'trimmed_length':str(wp.trimmed_length),
            u'recording':({
                u'mbid':uuid_b2h(track.recording_mbid_bin)
            } if track is not None else None),
            u'release':({
                u'mbid':release.mbid,
                u'title':release.title
            } if release is not None else None),
            u'source_type':wp.source_type,
            u'bit_rate':wp.bit_rate,
            u'bit_depth':wp.bit_depth,
            u'sample_rate':wp.sample_rate,
            u'num_channels':wp.num_channels,
            u'dr_level':wp.dr_level / 10,
            u'sonic_hash':wp.sonic_hash,
            u'track':({
                u'title':track.title,
                u'position':track.track_number,
                u'disc':track.disc_number,
                u'artist':track.artist_credit.name
            } if track is not None else None),
            u'preview':preview,
            u'sonic_hash':wp.sonic_hash
        }
    }

    session.close()

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

    required_data = {'recording', 'release', 'track', 'disc', 'image', 'source_type', 'sample_rate', 'bit_depth', 'bit_rate',
        'num_channels', 'length', 'length_trimmed', 'editor', 'dr_level'}

    l = [a for a in required_data if a not in f]
    if l:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Required data not provided. ({})".format(",".join(l))}))

    editor = session.query(Editor).filter_by(key=f['editor']).first()
    if editor is None:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Bad editor key ({})".format(f['editor'])}))

    image = waveplot.image.WavePlotImage(f['image'])

    wp.image_sha1 = image.sha1.digest()

    # Check for existing identical waveplot
    existing = session.query(WavePlot).filter_by(image_sha1 = image.sha1).first()
    if existing is not None:
        return make_response(json.dumps({u'result':u'exists', u'uuid':existing.uuid}))

    generated_uuid = uuid.uuid4()
    while session.query(WavePlot).filter_by(uuid = generated_uuid).count():
        generated_uuid = uuid.uuid4()

    wp.uuid_bin = generated_uuid.bytes

    wp.length = datetime.timedelta(seconds=int(f['length']))
    wp.trimmed_length = datetime.timedelta(seconds=int(f['length_trimmed']))

    image.generate_image_data()

    # Image Data in DB
    wp.thumbnail_bin = image.thumb_data
    wp.sonic_hash = image.sonic_hash
    print(wp.sonic_hash)

    # Sonic properties
    wp.num_channels = int(f['num_channels'])
    wp.dr_level = int(float(f['dr_level']) * 10)

    wp.source_type = f['source_type']
    wp.sample_rate = f['sample_rate']
    wp.bit_depth = f['bit_depth']
    wp.bit_rate = f['bit_rate']

    wpc = WavePlotContext(wp.uuid)

    wpc.release_mbid_bin = uuid_h2b(f['release'])
    wpc.recording_mbid_bin = uuid_h2b(f['recording'])
    wpc.track_number = f['track']
    wpc.disc_number = f['disc']

    image.save(generated_uuid.hex)

    session.add(wp)
    session.commit()
    session.add(wpc)

    e = Edit(editor_id = editor.id, waveplot_uuid_bin = wp.uuid_bin, edit_time = datetime.datetime.utcnow(), edit_type = 0)
    session.add(e)

    result_uuid = wp.uuid

    session.commit()
    session.close()

    return make_response(json.dumps({u'result':u'success', u'uuid':result_uuid}))
