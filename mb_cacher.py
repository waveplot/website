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


import waveplot.schema
from waveplot.schema import uuid_h2b, uuid_b2h, Artist, ArtistCredit, Artist_ArtistCredit, Release, Session, Track

waveplot.schema.setup()

last_query_time = datetime.datetime.now()

def query_mb(url):
    delta = datetime.datetime.now() - last_query_time

    if delta.seconds == 0:
        time.sleep(delta.microseconds / 1000000)

    r = requests.get(url)

    return r


def process_artist_credit(credit_data, session):
    credit_name = "".join(c['name']+c['joinphrase'] for c in credit_data)

    print("CRASH 1")

    db_credit = session.query(ArtistCredit).filter_by(name=credit_name).first()

    print("CRASH 2")

    print(credit_name)
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
        db_artist.last_cached = datetime.datetime.now()

        assoc = Artist_ArtistCredit()
        assoc.credit_name = credit['name']
        assoc.join_phrase = credit['joinphrase']
        assoc.position = pos

        assoc.child = db_credit

        db_artist.artist_credit_assocs.append(assoc)

    print("CRASH 3")

    session.commit()

    return db_credit

def update_release(release, session):
    url = ("http://musicbrainz.org/ws/2/release/" + release.mbid +
           "?inc=recordings artist-credits&fmt=json")

    try:
        r = query_mb(url)
    except requests.ConnectionError:
        return

    data = r.json()

    cache_time = datetime.datetime.now()

    release.title = data[u'title']
    release.last_cached = cache_time

    release.artist_credit = process_artist_credit(data[u'artist-credit'], session)

    update_tracks(release, data['media'], session)

    session.commit()

def update_tracks(release, media_data, session):
    for disc_num, medium in enumerate(media_data, start=1):
        for track_num, track in enumerate(medium['tracks'], start=1):
            source_db_track = session.query(Track).filter_by(track_number=track_num, disc_number = disc_num, release = release).first()

            if source_db_track is None:
                continue

            target_db_track = session.query(Track).filter_by(mbid_bin=uuid_h2b(track['id'])).first()
            if target_db_track is None:
                target_db_track = Track(track['id'], source_db_track.track_number, source_db_track.disc_number, source_db_track.release, source_db_track.recording)

            else:
                # Track exists - check if it's the real thing, or just a dummy mbid.
                if target_db_track.last_cached is None:
                    # It's not real - swap mbids.
                    source_db_track.mbid_bin, target_db_track.mbid_bin = target_db_track.mbid_bin, source_db_track.mbid_bin
                else:
                    # It is real - merge list of WavePlots then delete
                    target_db_track.waveplots.extend(source_db_track.waveplots)
                    session.delete(source_db_track)

            db_track = target_db_track

            for w in target_db_track.waveplots:
                w.track_mbid_bin = uuid_h2b(track['id'])

            db_track.title = track['title']
            db_track.last_cached = datetime.datetime.now()

            db_track.artist_credit = process_artist_credit(track['artist-credit'], session)

            session.commit()


def update_recording(recording, session):
    title = Column(UnicodeText(collation='utf8_bin'), nullable = True)
    waveplot_count = Column(Integer)
    last_cached = Column(DateTime, nullable = True)

    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'))


session = Session()

rel = session.query(Release).filter(Release.last_cached < datetime.datetime.now()).all()

print(rel)

for r in rel:
    update_release(r, session)
    #Fetch stuff

session.close()
