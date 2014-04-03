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
from flask.ext.sqlalchemy import SQLAlchemy

from waveplot.passwords import passwords
#from waveplot.schema import Editor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/waveplot_test'.format(passwords['mysql']['username'],passwords['mysql']['password'],passwords['mysql']['host'])
db = SQLAlchemy(app)

from waveplot.schema import Question, Editor

def add_cors_header(response):
    # https://github.com/jfinkels/flask-restless/issues/223
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost'
    response.headers['Access-Control-Allow-Methods'] = 'HEAD, GET, POST, PATCH, PUT, OPTIONS, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
    response.headers['Access-Control-Allow-Credentials'] = 'true'

    return response

manager = APIManager(app, flask_sqlalchemy_db=db)

app.after_request(add_cors_header)

VERSION = b'CITRUS'

import waveplot.json.editor
#import waveplot.json.homepage_data
import waveplot.json.recording
import waveplot.json.release
import waveplot.json.waveplot
import waveplot.json.question
import waveplot.json.artist
