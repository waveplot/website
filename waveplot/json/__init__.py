# -*- coding: utf8 -*-

# Copyright 2013, 2014 Ben Ockmore

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

from waveplot import app
from flask import jsonify, Blueprint

api_root_view = Blueprint('api_root_view', __name__)

@api_root_view.route('/api', methods = ['GET'])
def api_home():
    data = {
        "text":[
            "Welcome to the WavePlot API!",
            "This page is the landing page for the WavePlot API. You'll end "
            "up here if you visit the root of the API, and not one of the "
            "data pages. This document will explain how to use the API to "
            "retrieve data, and what sort of data can be retrieved.",
            "If you're new to web services, and want to try something out "
            "quickly, take a look at the following links:",
            {
                "List of Questions":"http://waveplot.net/api/question",
                "Sample Question":"http://waveplot.net/api/question/1"
            },
            "As you can see, each one returns a load of data in the JSON "
            "format. See:",
            "http://en.wikipedia.org/wiki/JSON",
            "There are 10 main types of object that it will be possible to "
            "query in this web-service. These are listed below, along with "
            "accepted HTTP methods (note - some of these may not yet be "
            "available):",
            {
                "Artist":["http://waveplot.net/api/artist","GET POST"],
                "Artist Credit":[
                    "http://waveplot.net/api/artist_credit",
                    "GET"
                ],
                "Artist - Artist Credit Relationship":[
                    "http://waveplot.net/api/artist_artist_credit",
                    "GET"
                ],
                "Edit":["http://waveplot.net/api/edit", "GET"],
                "Editor":["http://waveplot.net/api/editor", "GET POST PUT"],
                "Release":["http://waveplot.net/api/release", "GET POST"],
                "Recording":["http://waveplot.net/api/recording", "GET POST"],
                "Track":["http://waveplot.net/api/track", "GET POST PUT"],
                "WavePlot":[
                    "http://waveplot.net/api/waveplot",
                    "GET POST PUT"
                ],
                "Question":["http://waveplot.net/api/question", "GET POST"]
            },
            "A lot of these objects are designed to correspond exactly to a "
            "MusicBrainz entity. This explains why they only have GET and "
            "POST methods allowed - the server will automatically cache data "
            "from WavePlot, so no PUT is needed to update data.",
            "In general, you can POST on the list of objects (eg. /waveplot), "
            "PUT on an individual object (eg. /waveplot/1) and GET on either."
        ]
    }

    return jsonify(data)
