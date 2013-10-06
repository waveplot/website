#!/usr/bin/env python2
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

import datetime
import requests
import time
from collections import Counter

import waveplot.schema
from waveplot.schema import uuid_h2b, uuid_b2h, Artist, ArtistCredit, Artist_ArtistCredit, Release, Recording, Session, Track, WavePlot, WavePlotContext

waveplot.schema.setup()

last_query_time = datetime.datetime.utcnow()

def query_mb(url):
    delta = datetime.datetime.utcnow() - last_query_time

    if delta.seconds == 0:
        time.sleep(delta.microseconds / 1000000)

    r = requests.get(url)

    return r

def process_artist_credit(credit_data, session):
    # This should probably be replaced with an mbid-based method
    # Two artist credits which render the same will get mixed up.
    credit_name = "".join(c['name']+c['joinphrase'] for c in credit_data)

    db_credit = session.query(ArtistCredit).filter_by(name=credit_name).first()

    if db_credit is not None:
        return db_credit

    db_credit = ArtistCredit(credit_name)
    session.add(db_credit)


    for pos, credit in enumerate(credit_data):
        artist_data = credit['artist']
        db_artist = session.query(Artist).filter_by(mbid_bin=uuid_h2b(artist_data['id'])).first()

        if db_artist is None:
            db_artist = Artist(artist_data['id'])
            session.add(db_artist)

        db_artist.name = artist_data['name']
        db_artist.last_cached = datetime.datetime.utcnow()

        assoc = Artist_ArtistCredit()
        assoc.credit_name = credit['name']
        assoc.join_phrase = credit['joinphrase']
        assoc.position = pos

        assoc.child = db_credit

        db_artist.artist_credit_assocs.append(assoc)

    session.commit()

    return db_credit

def cache_track(track_mbid_bin, session, rel, track_num, disc_num, rec, track_data = None):
    if track_data is None:
        return

    track = session.query(Track).filter_by(mbid_bin = uuid_h2b(track_data['id'])).first()

    if track is None:
        track = Track(track_data['id'], track_num, disc_num, rel, rec)

    track.cache(track_data)
    track.artist_credit = process_artist_credit(track_data['artist-credit'],session)
    session.commit()

    return track

def cache_recording(recording_mbid_bin, session, recording_data = None):
    if recording_data is None:
        url = ("http://musicbrainz.org/ws/2/recording/" + uuid_b2h(recording_mbid_bin) +
                   "?inc=artist-credits&fmt=json")

        try:
            r = query_mb(url)
        except requests.ConnectionError:
            return

        recording_data = r.json()

    rec = session.query(Recording).filter_by(mbid_bin = uuid_h2b(recording_data['id'])).first()

    if rec is None:
        rec = Recording(recording_data['id'])
        session.add(rec)

    rec.cache(recording_data)
    rec.artist_credit = process_artist_credit(recording_data['artist-credit'], session)
    session.commit()

    return rec

def process_contexts_for_release(release_mbid_bin, session):
    url = ("http://musicbrainz.org/ws/2/release/"
           + uuid_b2h(release_mbid_bin) +
           "?inc=recordings artist-credits&fmt=json")

    try:
        r = query_mb(url)
    except requests.ConnectionError:
        return

    release_data = r.json()

    rel = session.query(Release).filter_by(mbid_bin = uuid_h2b(release_data['id'])).first()

    if rel is None:
        rel = Release(release_data['id'])
        session.add(rel)

    rel.cache(release_data)
    rel.artist_credit = process_artist_credit(release_data['artist-credit'], session)

    # Process contexts
    contexts = session.query(WavePlotContext).filter_by(release_mbid_bin = release_mbid_bin)

    for wpc in contexts:
        wp = session.query(WavePlot).filter_by(uuid_bin = wpc.uuid_bin).first()

        if wp is None:
            continue

        track_data = release_data['media'][wpc.disc_number - 1]['tracks'][wpc.track_number - 1]
        recording_data = track_data['recording']
        recording_mbid_bin = uuid_h2b(recording_data['id'])

        if wpc.recording_mbid_bin != recording_mbid_bin:
            continue

        # Perfect Match, continue
        rec = cache_recording(wpc.recording_mbid_bin, session, recording_data)
        track = cache_track(None, session, rel, wpc.track_number, wpc.disc_number, rec, track_data)

        wp.recording = rec
        wp.track = track

        session.delete(wpc) # Remove the wpc if it's been processed

    rel.calculate_dr()
    session.commit()


session = Session()

contexts = session.query(WavePlotContext).all()

new_release_mbids = Counter(wpc.release_mbid_bin for wpc in contexts)

for rel_mbid, count in new_release_mbids.most_common():
    process_contexts_for_release(rel_mbid, session)

session.close()
