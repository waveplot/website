#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
from waveplot.passwords import passwords

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

def secsToHMS(secs):
    mins = secs // 60
    secs -= 60 * mins

    hours = mins // 60
    mins -= 60 * hours
    return "{:02.0f}:{:02.0f}:{:02.0f}".format(hours, mins, secs)

def get_cursor(db_con, use_dict = False):
    try:
        if use_dict:
            result = db_con.cursor(db.cursors.DictCursor)
        else:
            result = db_con.cursor()

        result.execute("USE waveplot")
        db_con.commit()

        return result
    except db.OperationalError:
        db_con = db.connect(host = "localhost", user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot', use_unicode = True, charset = "utf8")

        if use_dict:
            result = db_con.cursor(db.cursors.DictCursor)
        else:
            result = db_con.cursor()

        result.execute("USE waveplot")
        db_con.commit()

        return result

def crossdomain(origin = None, methods = None, headers = None,
                max_age = 21600, attach_to_all = True,
                automatic_options = True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
