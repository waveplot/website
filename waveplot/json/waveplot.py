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
from flask import abort, jsonify, Blueprint

from flask.ext.restless import ProcessingException

import waveplot.schema
import waveplot.utils
import waveplot.image

from waveplot import manager, VERSION

from waveplot.schema import db, WavePlot, Editor

def pre_post(data=None, **kw):
    if data.get('version', None) != VERSION:
        raise ProcessingException(message='Incorrect WavePlot Version - Update Client',
                                  status_code=403)

    editor = db.session.query(Editor).filter_by(key=data['editor']).first()
    if editor is None:
        raise ProcessingException(message='Invalid Editor Key',
                                  status_code=403)

    data['editor'] = editor.id

    image = waveplot.image.WavePlotImage(data['image'])

    data['image_sha1'] = image.sha1.digest()

    existing = db.session.query(WavePlot).filter_by(image_sha1 = data['image_sha1']).first()
    if existing is not None:
        raise ProcessingException(message=existing.uuid,
                                  status_code=303)

    generated_uuid = uuid.uuid4()
    while db.session.query(WavePlot).filter_by(uuid = unicode(generated_uuid.hex)).count():
        generated_uuid = uuid.uuid4()

    data['uuid'] = str(generated_uuid)

    data['dr_level'] = int(float(data['dr_level']) * 10)

    image.generate_image_data()

    data['thumbnail'] = image.thumb_data
    data['sonic_hash'] = image.sonic_hash

    data['length'] = datetime.timedelta(seconds=int(data['length']))
    data['trimmed_length'] = image.trimmed_length

    image.save(generated_uuid.hex)

    data['edits'] = [{
        "edit_time":datetime.datetime.utcnow().isoformat(),
        "edit_type":0,
        "editor_id":data['editor'],
        "waveplot_uuid":data['uuid']
    }]

    # Delete once it's saved
    del data['image']
    del data['editor']

def post_post(result=None, **kw):
    result['thumbnail'] = base64.b64encode(result['thumbnail'])
    result['image_sha1'] = base64.b64encode(result['image_sha1'])
    result['length'] = str(result['length'])
    result['trimmed_length'] = str(result['trimmed_length'])
    result['dr_level'] = result['dr_level'] / 10

def post_get(result=None, **kw):
    result['thumbnail'] = base64.b64encode(result['thumbnail'])
    result['image_sha1'] = base64.b64encode(result['image_sha1'])
    result['length'] = str(result['length'])
    result['trimmed_length'] = str(result['trimmed_length'])
    result['dr_level'] = result['dr_level'] / 10

def post_get_many(result=None, search_params=None, **kw):
    for w in result['objects']:
        w['thumbnail'] = base64.b64encode(w['thumbnail'])
        w['image_sha1'] = base64.b64encode(w['image_sha1'])
        w['length'] = str(w['length'])
        w['trimmed_length'] = str(w['trimmed_length'])
        w['dr_level'] = w['dr_level'] / 10


manager.create_api(WavePlot, methods=['GET', 'POST'],
                   preprocessors={
                       'POST':[pre_post],
                   },
                   postprocessors={
                       'GET_SINGLE':[post_get],
                       'GET_MANY':[post_get_many],
                       'POST':[post_post],
                   }
)


waveplot_views = Blueprint('waveplot_views', __name__)

@waveplot_views.route('/api/waveplot/<id>/preview', methods = ['GET'])
def waveplot_preview(id):
    id = uuid.UUID(id).hex

    try:
        with open(os.path.join("./static/images/waveplots/previews",id[:3],id), 'rb') as f:
            data = f.read()
    except IOError:
        abort(404)

    return jsonify({'data':base64.b64encode(data)})


@waveplot_views.route('/api/waveplot/<id>/full', methods = ['GET'])
def waveplot_full(id):
    id = uuid.UUID(id).hex

    try:
        with open(os.path.join("./static/images/waveplots/full",id[:3],id), 'rb') as f:
            data = f.read()
    except IOError:
        abort(404)

    return jsonify({'data':base64.b64encode(data)})

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

    #Calculate this - wp.trimmed_length = datetime.timedelta(seconds=int(f['length_trimmed']))


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
