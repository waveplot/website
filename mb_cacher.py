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
from waveplot.schema import Artist, ArtistCredit, ArtistArtistCredit, Release, Recording, Track, WavePlot, WavePlotContext, db

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
        return None

    data = response.json()

    for key in {'id','name'}:
        if key not in data:
            return None

    # Handle merging of recordings
    if artist.mbid != data['id']:
        change_artist_mbid(artist, data['id'])

    artist.name = data['name']
    artist.last_cached = datetime.datetime.utcnow()

    db.session.commit()

    return data

def cache_recording(recording):
    url = (
        'http://musicbrainz.org/ws/2/recording/{}'
        '?inc=artist-credits&fmt=json'
    ).format(recording.mbid)

    response = query_mb(url)

    if response.status_code != 200:
        return None

    data = response.json()

    for key in {'id','title'}:
        if key not in data:
            return None

    # Handle merging of recordings
    if recording.mbid != data['id']:
        change_recording_mbid(recording, data['id'])

    recording.title = data['title']
    recording.last_cached = datetime.datetime.utcnow()

    db.session.commit()

    recording.artist_credit = process_artist_credit(data['artist-credit'])
    db.session.commit()

    return data

def cache_track(track, data):
    media = data['media']

    if track.disc_number > len(media):
        return None
    medium = media[track.disc_number - 1]

    tracks = medium['tracks']

    if track.track_number > len(tracks):
        return None
    track_data = tracks[track.track_number - 1]

    if track.mbid != track_data['id']:
        # Not sure what to do here yet, so leave uncached
        return None

    track.title = track_data['title']
    track.last_cached = datetime.datetime.utcnow()

    db.session.commit()

    track.artist_credit = process_artist_credit(track_data['artist-credit'])

    db.session.commit()

    return data

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
            return None

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

    return data

def cache_context(context):
    # Attempt to get the track
    track = (
        db.session.query(Track).filter_by(mbid=context.track_mbid).first()
        if context.track_mbid is not None
        else None
    )

    # If the track doesn't exist, we need to obtain the release data
    # Release must be present first, so ensure that
    if track is None:
        if context.release_mbid is None:
            # If release is None, no way of linking - delete link and return
            db.session.delete(context)
            db.session.commit()
            return

        release = db.session.query(Release).filter_by(mbid=context.release_mbid).first()

        if release is None:
            release = Release(context.release_mbid)
            db.session.add(release)
            db.session.commit()

        # Cache and use returned data to create tracks
        data = cache_release(release)
        # Update context in case release mbid has changed
        context.release_mbid = release.mbid

        # Get correct mbid, track number and disc number in context
        track_data = None
        if ((context.disc_number is not None) and
                (context.track_number is not None)):
            media = data['media']

            if context.disc_number > len(media):
                return
            medium = media[context.disc_number - 1]

            tracks = medium['tracks']

            if context.track_number > len(tracks):
                return None
            track_data = tracks[context.track_number - 1]

            if context.track_mbid is not None:
                if context.track_mbid != track_data['id']:
                    # Submitted link is out of date
                    db.session.delete(context)
                    db.session.commit()
                    return
            context.track_mbid = track_data['id']
        elif context.track_mbid is not None:
            media = data['media']

            for disc_index, medium in enumerate(media):
                for track_index, track in enumerate(medium['tracks']):
                    if track['id'] == context.track_mbid:
                        context.track_number = track_index + 1
                        context.disc_number = disc_index + 1
                        track_data = track
                        break
                if track_data is not None:
                    break
        else:
            db.session.delete(context)
            db.session.commit()
            return

        if context.recording_mbid is not None:
            if context.recording_mbid != track_data['recording']['id']:
                db.session.delete(context)
                db.session.commit()
                return

        context.recording_mbid = track_data['recording']['id']

        # If recording doesn't exist, create blank recording with correct mbid
        recording = db.session.query(Recording).filter_by(mbid=context.recording_mbid).first()

        if recording is None:
            recording = Recording(context.recording_mbid)
            db.session.add(recording)
            db.session.commit()

        # At this point, the release_mbid, recording_mbid, track_number, disc_number
        # and track_mbid have been set. Release and recording both exist in the database.
        # We can now create the track, if the track mbid is still unable to be found.

        track = db.session.query(Track).filter_by(mbid=context.track_mbid).first()
        if track is None:
            track = Track(context.track_mbid, context.track_number, context.disc_number, context.release_mbid, context.recording_mbid)
            print(track.mbid)
            print(track.release_mbid)
            print(track.recording_mbid)
            db.session.add(track)
            db.session.commit()

        # Finally, cache the track, passing in the track data structure as is
        # done in the cache_release procedure
        cache_track(track, data)

    print("Successfully got track {}".format(track.mbid))

    # We now have a created track. Link this to the WavePlot.

    # This one's a foreign key, so no need to check the returned WavePlot.
    waveplot = db.session.query(WavePlot).filter_by(uuid=context.waveplot_uuid).first()
    if waveplot not in track.waveplots:
        track.waveplots.append(waveplot)

    db.session.delete(context)
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

        context = db.session.query(WavePlotContext).first()
        if context is not None:
            idle = False
            cache_context(context)

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
