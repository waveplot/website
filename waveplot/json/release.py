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
from waveplot.schema import Session, Release

@app.route('/json/release', methods = ['GET'])
@waveplot.utils.crossdomain(origin = '*')
def release():
    offset = int(request.args.get('offset', "0"))
    limit = int(request.args.get('limit', "24"))

    session = Session()

    releases = session.query(Release).order_by(Release.title.asc()).offset(offset).limit(limit)

    data = [
        {
            'id':r.mbid,
            'title':r.title,
            'url':None
        } for r in releases.all()
    ]

    session.close()

    return make_response(json.dumps(data))

@app.route('/json/extreme-dr', methods = ['GET'])
@waveplot.utils.crossdomain(origin = '*')
def extreme_dr():

    session = Session()

    releases = session.query(Release).order_by(Release.dr_level.desc()).limit(10)

    highest = [{u'title':r.title, u'artist':r.artist_credit.name, u'mbid':r.mbid, u'dr_level':r.dr_level / 10} for r in releases]

    releases = session.query(Release).order_by(Release.dr_level.asc()).limit(10)

    lowest = [{u'title':r.title, u'artist':r.artist_credit.name, u'mbid':r.mbid, u'dr_level':r.dr_level / 10} for r in releases]

    session.close()

    return make_response(json.dumps({u'highest':highest, u'lowest':lowest}))
