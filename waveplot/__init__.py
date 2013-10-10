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

import os

from flask import Flask

import waveplot.schema

VERSION = b'CITRUS'

waveplot.schema.setup()

app = Flask(__name__)
app.config.from_object('waveplot.default_settings')
if os.getenv('WAVEPLOT_SETTINGS') is not None:
    app.config.from_envvar('WAVEPLOT_SETTINGS')



import waveplot.json.editor
import waveplot.json.recording
import waveplot.json.release
import waveplot.json.waveplot
