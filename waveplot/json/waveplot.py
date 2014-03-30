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

from flask.ext.restless import ProcessingException

import waveplot.schema
import waveplot.utils
import waveplot.image

from waveplot import manager, db, VERSION

from waveplot.schema import WavePlot

def pre_post(data=None, **kw):
    if data.get('version', None) != VERSION:
        raise ProcessingException(message='Incorrect WavePlot Version - Update Client',
                                  status_code=403)

    image = waveplot.image.WavePlotImage(data['image'])

    data['image_sha1'] = image.sha1.digest()

    existing = db.session.query(WavePlot).filter_by(image_sha1 = image.sha1).first()
    if existing is not None:
        data['uuid'] = existing.uuid
        return

    generated_uuid = uuid.uuid4()
    while db.session.query(WavePlot).filter_by(uuid = unicode(generated_uuid.hex)).count():
        generated_uuid = uuid.uuid4()

    data['uuid'] = generated_uuid.hex

    data['dr_level'] = int(float(data['dr_level']) * 10)

    image.generate_image_data()

    data['thumbnail'] = image.thumb_data
    data['sonic_hash'] = image.sonic_hash

    data['length'] = datetime.timedelta(seconds=int(data['length']))
    data['trimmed_length'] = data['length']

    # Delete once it's saved
    del data['image']
    del data['editor']

def post_post(result=None, **kw):
    #wp.submit_date = datetime.datetime.utcnow()
    pass

def post_get(result=None, **kw):
    result['thumbnail'] = base64.b64encode(result['thumbnail'])

manager.create_api(WavePlot, methods=['GET', 'POST'],
                   preprocessors={
                       'POST':[pre_post]
                   }
)

def waveplot_get_uuid(value):

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

def waveplot_post():
    if request.form.get('version', None) != VERSION:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Incorrect client version or no version provided."}))

    session = Session()

    wp = WavePlot()
    wp.version = VERSION
    wp.submit_date = datetime.datetime.utcnow()

    f = request.form.to_dict()

    required_data = {
        'image',
        'source_type',
        'sample_rate',
        'bit_depth',
        'bit_rate',
        'num_channels',
        'length',
        'editor',
        'dr_level'
    }

    l = [a for a in required_data if a not in f]
    if l:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Required data not provided. ({})".format(",".join(l))}))

    #editor = session.query(Editor).filter_by(key=f['editor']).first()
    #if editor is None:
        #return make_response(json.dumps({u'result':u'failure', u'error':u"Bad editor key ({})".format(f['editor'])}))

    # Check for existing identical waveplot
    generated_uuid = uuid.uuid4()
    while session.query(WavePlot).filter_by(uuid = generated_uuid).count():
        generated_uuid = uuid.uuid4()

    wp.uuid_bin = generated_uuid.bytes

    wp.length = datetime.timedelta(seconds=int(f['length']))
    #Calculate this - wp.trimmed_length = datetime.timedelta(seconds=int(f['length_trimmed']))

    image.generate_image_data()

    # Image Data in DB
    wp.thumbnail_bin = image.thumb_data
    wp.sonic_hash = image.sonic_hash

    # Sonic properties
    wp.num_channels = int(f['num_channels'])
    wp.dr_level = int(float(f['dr_level']) * 10)

    image.save(generated_uuid.hex)

    session.add(wp)
    session.commit()

    e = Edit(editor_id = editor.id, waveplot_uuid_bin = wp.uuid_bin, edit_time = datetime.datetime.utcnow(), edit_type = 0)
    session.add(e)

def waveplot_put_uuid(value):
    required_data = {'recording', 'release', 'track', 'disc', 'editor'}

    l = [a for a in required_data if a not in f]
    if l:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Required data not provided. ({})".format(",".join(l))}))

    editor = session.query(Editor).filter_by(key=f['editor']).first()
    if editor is None:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Bad editor key ({})".format(f['editor'])}))

    wpc = WavePlotContext(uuid_h2b(value))

    wpc.release_mbid_bin = uuid_h2b(f['release'])
    wpc.recording_mbid_bin = uuid_h2b(f['recording'])
    wpc.track_number = f['track']
    wpc.disc_number = f['disc']
    session.add(wpc)
    session.commit()

    e = Edit(editor_id = editor.id, waveplot_uuid_bin = wp.uuid_bin, edit_time = datetime.datetime.utcnow(), edit_type = 1)
    session.add(e)
    session.commit()

    return make_response(json.dumps({u'result':u'success', u'uuid':value}))
