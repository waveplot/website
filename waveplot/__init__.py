#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import os
import json

VERSION = b'CITRUS'
lookup_thread = None

from flask import Flask, redirect, url_for, make_response
import waveplot.musicbrainz_lookup

app = Flask(__name__)
app.config.from_object('waveplot.default_settings')
if os.getenv('WAVEPLOT_SETTINGS') is not None:
    app.config.from_envvar('WAVEPLOT_SETTINGS')

#This seems like a very hacky thing to do. Need to avoid running the thread twice though. Suggestions?
@app.before_first_request
def start_lookup_thread():
    global lookup_thread
    lookup_thread = waveplot.musicbrainz_lookup.LookupThread()
    lookup_thread.setDaemon(True)
    lookup_thread.start()


import waveplot.json.recording
import waveplot.json.waveplot
import waveplot.json.release

@app.route("/")
def home():
    return make_response(open("./waveplot/static/index.html","r").read())