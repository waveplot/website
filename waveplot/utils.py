#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
from waveplot.passwords import passwords

from flask import request

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
        db_con = db.connect(host="localhost",user=passwords['mysql']['username'], passwd=passwords['mysql']['password'], db='waveplot', use_unicode = True, charset = "utf8")

        if use_dict:
            result = db_con.cursor(db.cursors.DictCursor)
        else:
            result = db_con.cursor()

        result.execute("USE waveplot")
        db_con.commit()

        return result

CROSS_DOMAIN_ALLOWED = ['http://localhost', 'http://pi.ockmore.net', 'http://waveplot.ockmore.net']

def check_cross_domain(response):
    origin = request.headers.get('Origin',None)

    if origin in CROSS_DOMAIN_ALLOWED:
        response.headers['Access-Control-Allow-Origin'] = origin
        return True

    return False