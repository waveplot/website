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
import random

from flask import request, make_response

import waveplot.schema
import waveplot.utils

from waveplot import app
from waveplot.schema import Session, Editor

@app.route('/json/editor', methods = ['POST', 'OPTIONS'])
@waveplot.utils.crossdomain(origin = '*')
def editor_all():
    if request.method == b'POST':
        return editor_create()

@app.route("/json/activate", methods = ['POST'])
@waveplot.utils.crossdomain(origin = '*')
def activate():
    if 'key' not in request.form:
        return make_response(json.dumps({u'result':u'failure', u'error':u"Missing data. Activation key required."}))

    session = Session()

    editor = session.query(Editor).filter_by(key=request.form['key']).first()

    if editor is None:
        return make_response(json.dumps({u'result':u'failure', u'error':u"No such key! Please register!"}))

    if editor.activated:
        return make_response(json.dumps({u'result':u'failure', u'error':u"You've already activated! Time to use the site!"}))

    editor.activated = True

    session.commit()

    return make_response(json.dumps({u'result':u'success'}))


def editor_create():
    activation_string = """
<p>Hi {}!</p>

<p>Please activate your WavePlot account using the activation link below:</p>

<p><a href="{}">{}</a></p>

<p>Many thanks for your help in building the WavePlot database!</p>"""


    username = request.form.get('username', '')
    email = request.form.get('email', '')

    if not (username and email):
        return make_response(json.dumps({u'result':u'failure', u'error':u"Missing data. Username and email required."}))

    atpos = email.rfind('@')
    dotpos = email.rfind('.')

    if (atpos < 1) or (dotpos < (atpos + 2)) or ((dotpos + 2) >= len(email)):
        return make_response(json.dumps({u'result':u'failure', u'error':u"Email address invalid."}))

    session = Session()

    if session.query(Editor).filter_by(email=email).count():
        return make_response(json.dumps({u'result':u'failure', u'error':u"Email address already registered. Please await your activation email."}))

    generated_key = random.randint(0, 999999999)
    while session.query(Editor).filter_by(key=generated_key).count():
        generated_key = random.randint(0, 999999999)

    new_editor = Editor(username, email, generated_key)
    session.add(new_editor)

    # Send an activation email
    activation_url = "http://waveplot.ockmore.net/#/activate/"+str(generated_key)
    waveplot.utils.SendEmail(email,"WavePlot Activation Required!", activation_string.format(username,activation_url,activation_url))

    response = make_response(json.dumps({u'result':u'success'}))

    session.commit()

    return make_response(json.dumps({u'result':u'success'}))
