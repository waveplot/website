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

from flask import request, make_response

import waveplot.schema
import waveplot.utils

from waveplot import app
from waveplot.schema import Session, Recording

@app.route('/json/recording/<value>', methods = ['GET', 'PUT'])
@waveplot.utils.crossdomain(origin = '*')
def recording_all(value):
    if value.startswith("list"):
        return recording_list()
    else:
        return recording_mbid_get(value)


def recording_mbid_get(value):
    session = Session()

    recording = session.query(Recording).filter_by(mbid=value).first()

    if recording is None:
        return make_response(json.dumps({u'result':u'failure', u'error':u"No such recording!"}))

    tracks = recording.tracks

    results = {u'mbid':value, u'waveplots':[]}

    for track in tracks:
        results[u'waveplots'].extend({u'uuid':w.uuid, u'audio_barcode':w.audio_barcode} for w in track.waveplots)

    return make_response(json.dumps(results))

def recording_list():
    session = Session()

    min_linked_waveplots = int(request.args.get('linked-waveplots', "1"))
    page = int(request.args.get('page', "1"))
    limit = int(request.args.get('limit', "20"))

    offset = (page - 1) * limit

    recordings = session.query(Recording).filter(Recording.waveplot_count >= min_linked_waveplots).offset(offset).limit(limit)

    results = [{u"mbid":r.mbid, u'count':r.waveplot_count} for r in recordings]

    return make_response(json.dumps(results))
