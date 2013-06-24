#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db
import json

from flask import request, Response, make_response

from waveplot import app
from waveplot.passwords import passwords

import waveplot.utils

db_con = db.connect(host = "localhost", user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot', use_unicode = True, charset = "utf8")

@app.route('/json/extreme-dr', methods = ['GET'])
def extreme_dr():
    cur = waveplot.utils.get_cursor(db_con)

    cur.execute("SELECT releases.cached_title, artist_credits.name, releases.mbid, releases.dr_level FROM releases JOIN artist_credits ON releases.cached_artist_credit=artist_credits.id ORDER BY dr_level DESC LIMIT 10")
    rows = cur.fetchall()

    info = [u'title', u'artist', u'mbid', u'dr_level']

    highest = [dict(zip(info, row)) for row in rows]

    for result in highest:
        result[b'dr_level'] = result[b'dr_level'] / 10

        # release[b"short_cached_artist"] = release["cached_artist"]

        # if len(release["cached_name"]) > 30:
            # release["cached_name"] = release["cached_name"][0:30] + u"..."
        # if len(release["cached_artist"]) > 30:
         #   release["short_cached_artist"] = release["cached_artist"][0:30] + u"..."

    cur.execute("SELECT releases.cached_title, artist_credits.name, releases.mbid, releases.dr_level FROM releases JOIN artist_credits ON releases.cached_artist_credit=artist_credits.id ORDER BY dr_level ASC LIMIT 10")
    rows = cur.fetchall()

    lowest = [dict(zip(info, row)) for row in reversed(rows)]

    for result in lowest:
        result[b'dr_level'] = result[b'dr_level'] / 10

    response = make_response(json.dumps({u'highest':highest, u'lowest':lowest}))
    waveplot.utils.check_cross_domain(response)

    return response
