#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
import json
import random

from flask import request, make_response

from waveplot import app
from waveplot.passwords import passwords

import waveplot.utils

db_con = db.connect(host = "localhost", user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot', use_unicode = True, charset = "utf8")

activation_string = """
<p>Hi {}!</p>

<p>Please activate your WavePlot account using the activation link below:</p>

<p><a href="{}">{}</a></p>

<p>Many thanks for your help in building the WavePlot database!</p>"""

def editor_create():
    username = request.form.get('username', '')
    email = request.form.get('email', '')

    if username and email:
        atpos = email.rfind('@')
        dotpos = email.rfind('.')

        if (atpos < 1) or (dotpos < (atpos + 2)) or ((dotpos + 2) >= len(email)):
            response = make_response(json.dumps({u'result':u'failure', u'error':u"Email address invalid."}))
            return response

        cur = waveplot.utils.get_cursor(db_con)
        cur.execute("SELECT * FROM editors WHERE email=%s", (email,))
        rows = cur.fetchall()

        if not rows:
            generated_key = random.randint(0, 999999999)
            cur.execute("SELECT activation_key FROM editors WHERE activation_key=%s", (generated_key,))
            while cur.fetchall():
                generated_key = random.randint(0, 999999999)
                cur.execute("SELECT activation_key FROM editors WHERE activation_key=%s", (generated_key,))

            cur.execute("INSERT INTO editors (name,email,activation_key) VALUES (%s,%s,%s)", (username, email, generated_key))
            db_con.commit()

            # Send an activation email
            activation_url = "http://waveplot.ockmore.net/#/activate/"+str(generated_key)
            waveplot.utils.SendEmail(email,"WavePlot Activation Required!", activation_string.format(username,activation_url,activation_url))

            response = make_response(json.dumps({u'result':u'success'}))
        else:
            response = make_response(json.dumps({u'result':u'failure', u'error':u"Email address already registered. Please await your activation email."}))
    else:
        response = make_response(json.dumps({u'result':u'failure', u'error':u"Missing data. Username and email required."}))

    return response

@app.route('/json/editor', methods = ['POST', 'OPTIONS'])
@waveplot.utils.crossdomain(origin = '*')
def editor_all():
    if request.method == b'POST':
        return editor_create()

@app.route("/json/activate", methods = ['POST'])
@waveplot.utils.crossdomain(origin = '*')
def activate():
    key = request.form.get('key', None)
    if key is None:
        response = make_response(json.dumps({u'result':u'failure', u'error':u"Missing data. Activation key required."}))

    cur = waveplot.utils.get_cursor(db_con)
    cur.execute("SELECT activation_key, activated FROM editors WHERE activation_key=%s", (key,))
    rows = cur.fetchall()
    if rows:
        if not rows[0][1]:
            cur.execute("UPDATE editors SET activated = 1 WHERE activation_key = %s", (key,))
            response = make_response(json.dumps({u'result':u'success'}))
        else:
            response = make_response(json.dumps({u'result':u'failure', u'error':u"You've already activated! Time to use the site!"}))
    else:
        response = make_response(json.dumps({u'result':u'failure', u'error':u"No such key! Please register!"}))

    return response

