#!/usr/bin/env python2
# -*- coding: utf8 -*-

# Copyright 2014 Ben Ockmore

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
import json
from collections import Counter, defaultdict

from sqlalchemy import func

import waveplot.schema
from waveplot.schema import Artist, ArtistCredit, ArtistArtistCredit, Release, Recording, Track, WavePlot, db

from waveplot import create_app
from waveplot.passwords import passwords

last_query_time = datetime.datetime.utcnow()

def pprint(data):
     return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

def query_mb(url):
    global last_query_time

    delta = datetime.datetime.utcnow() - last_query_time

    if delta.seconds == 0:
        time.sleep(1.0 - (float(delta.microseconds) / 1000000.0))

    last_query_time = datetime.datetime.utcnow()
    r = requests.get(url)

    return r

def get_artist_credit_for_data(data):
    credit_name = "".join(c['name']+c['joinphrase'] for c in data)

    for m in db.session.query(ArtistCredit).filter_by(name=credit_name):
        # Check that mbids match
        for assoc in m.artist_assocs:
            if data[assoc.position]['artist']['id'] != assoc.artist_mbid:
                raise LookupError

        return m

    raise LookupError

def create_artist_credit(data):
    # Create new artists
    artists = [x['artist'] for x in data]
    for artist in artists:
        if db.session.query(Artist).filter_by(mbid=artist['id']).first() is not None:
            continue

        new_artist = Artist(artist['id'], artist['name'])
        new_artist.last_cached = datetime.datetime.utcnow()
        db.session.add(new_artist)
        db.session.commit()

    # Create artist credit
    credit_name = "".join(c['name']+c['joinphrase'] for c in data)
    new_credit = ArtistCredit(credit_name)
    new_credit.last_cached = datetime.datetime.utcnow()
    db.session.add(new_credit)
    db.session.commit()

    # Create associations
    for i, credit in enumerate(data):
        new_assoc = ArtistArtistCredit(credit['name'], credit['joinphrase'], i, new_credit.id, credit['artist']['id'])
        db.session.add(new_assoc)
        db.session.commit()

    return new_credit

def process_artist_credit(data):
    try:
        return get_artist_credit_for_data(data)
    except LookupError:
        return create_artist_credit(data)

def change_artist_mbid(artist, new_mbid):
    pass

def change_recording_mbid(recording, new_mbid):
    # Create new recording with the same data and relationships but
    # different primary key, then delete old recording
    pass

def change_release_mbid(release, new_mbid):
    pass

def cache_artist(artist):
    url = (
        'http://musicbrainz.org/ws/2/artist/{}'
        '?fmt=json'
    ).format(artist.mbid)

    response = query_mb(url)

    if response.status_code != 200:
        return

    data = response.json()

    for key in {'id','name'}:
        if key not in data:
            return

    # Handle merging of recordings
    if artist.mbid != data['id']:
        change_artist_mbid(artist, data['id'])

    artist.name = data['name']
    artist.last_cached = datetime.datetime.utcnow()

    db.session.commit()

def cache_recording(recording):
    url = (
        'http://musicbrainz.org/ws/2/recording/{}'
        '?inc=artist-credits&fmt=json'
    ).format(recording.mbid)

    response = query_mb(url)

    if response.status_code != 200:
        return

    data = response.json()

    for key in {'id','title'}:
        if key not in data:
            return

    # Handle merging of recordings
    if recording.mbid != data['id']:
        change_recording_mbid(recording, data['id'])

    recording.title = data['title']
    recording.last_cached = datetime.datetime.utcnow()

    db.session.commit()

    recording.artist_credit = process_artist_credit(data['artist-credit'])
    db.session.commit()

def cache_track(track, data):
    media = data['media']

    if track.disc_number > len(media):
        return
    medium = media[track.disc_number - 1]

    tracks = medium['tracks']

    if track.track_number > len(tracks):
        return
    track_data = tracks[track.track_number - 1]

    if track.mbid != track_data['id']:
        # Not sure what to do here yet, so leave uncached
        return

    track.title = track_data['title']
    track.last_cached = datetime.datetime.utcnow()

    db.session.commit()

    track.artist_credit = process_artist_credit(track_data['artist-credit'])

    db.session.commit()

def cache_release(release):
    url = (
        'http://musicbrainz.org/ws/2/release/{}'
        '?inc=recordings artist-credits&fmt=json'
    ).format(release.mbid)

    response = query_mb(url)

    if response.status_code != 200:
        return

    data = response.json()

    for key in {'id', 'title'}:
        if key not in data:
            return

    # Handle merging of releases
    if release.mbid != data['id']:
        change_release_mbid(release, data['id'])

    release.title = data['title']
    release.last_cached = datetime.datetime.utcnow()

    db.session.commit()

    release.artist_credit = process_artist_credit(data['artist-credit'])

    db.session.commit()

    for track in release.tracks:
        cache_track(track, data)

    db.session.commit()

def main():
    config = {
        'SQLALCHEMY_DATABASE_URI':'mysql://{}:{}@{}/waveplot_test'.format(passwords['mysql']['username'],passwords['mysql']['password'],passwords['mysql']['host'])
    }

    uncached_mbid_requests = defaultdict(int)

    app = create_app(config)

    idle = False

    while 1:
        if idle:
            time.sleep(5) # Sleep for 30 seconds if things haven't just been processing

        idle = True
        rec = db.session.query(Recording).filter_by(last_cached=None).first()
        if rec is not None:
            idle = False
            if uncached_mbid_requests[rec.mbid] < 10:
                print(rec.mbid)
                try:
                    cache_recording(rec)
                except requests.exceptions.ConnectionError:
                    time.sleep(5)
            else:
                print("Not requesting {} - too many repeats!".format(rec.mbid))
            uncached_mbid_requests[rec.mbid] += 1

        rel = db.session.query(Release).filter_by(last_cached=None).first()
        if rel is not None:
            idle = False
            if uncached_mbid_requests[rel.mbid] < 10:
                print(rel.mbid)
                try:
                    cache_release(rel)
                except requests.exceptions.ConnectionError:
                    time.sleep(5)
            else:
                print("Not requesting {} - too many repeats!".format(rel.mbid))
            uncached_mbid_requests[rel.mbid] += 1

        artist = db.session.query(Artist).filter_by(last_cached=None).first()
        if artist is not None:
            idle = False
            if uncached_mbid_requests[artist.mbid] < 10:
                print(artist.mbid)
                try:
                    cache_artist(artist)
                except requests.exceptions.ConnectionError:
                    time.sleep(5)
            else:
                print("Not requesting {} - too many repeats!".format(artist.mbid))
            uncached_mbid_requests[artist.mbid] += 1

        """rec = db.session.query(Recording).filter(Recording.last_cached != None).order_by(Recording.last_cached).first()
        if rec is not None:
            idle = False
            print(rec.mbid)
            cache_recording(rec)

        rel = db.session.query(Release).filter(Release.last_cached != None).order_by(Release.last_cached).first()
        if rel is not None:
            idle = False
            print(rel.mbid)
            cache_release(rel)"""

main()
