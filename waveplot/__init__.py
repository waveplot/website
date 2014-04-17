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

from flask import Flask
from flask.ext.restless import APIManager

VERSION = b'CITRUS'

manager = APIManager()

def add_cors_header(response):
    # https://github.com/jfinkels/flask-restless/issues/223
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'HEAD, GET, POST, PATCH, PUT, OPTIONS, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
    response.headers['Access-Control-Allow-Credentials'] = 'true'

    return response

def create_app(config):
    app = Flask(__name__)
    app.config.update(config)
    app.after_request(add_cors_header)

    print("Application created with the following config:")
    for k,v in app.config.items():
        print("{} = {}".format(k,v))

    from waveplot.schema import db
    db.init_app(app)

    global manager
    manager.init_app(app, flask_sqlalchemy_db=db)

    from waveplot.json.waveplot import waveplot_views
    app.register_blueprint(waveplot_views)

    from waveplot.json.homepage_data import homepage_data_views
    app.register_blueprint(homepage_data_views)

    return app
