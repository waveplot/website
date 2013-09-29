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

import uuid
import base64
import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import Column, Integer, BigInteger, UnicodeText, Boolean, SmallInteger, BINARY, ForeignKey, Interval, String, DateTime

from waveplot.passwords import passwords

Base = declarative_base()
Session = sessionmaker()

def uuid_b2h(b):
    return str(uuid.UUID(bytes=b))

def uuid_h2b(h):
    return uuid.UUID(hex=h).bytes

def mbid_get(self):
    return uuid_b2h(self.mbid_bin)

def mbid_set(self, value):
    self.mbid_bin = uuid_h2b(value)

class Editor(Base):
    __tablename__ = 'editors'

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText(collation='utf8_bin'))
    email = Column(UnicodeText(collation='utf8_bin'))
    queries_per_min = Column(Integer, default=60)
    key = Column(BigInteger)
    activated = Column(Boolean)

    waveplots = relationship("WavePlot", backref="editor")

    def __init__(self, name, email, key, activated = False):
        self.name = name
        self.email = email
        self.key = key
        self.activated = activated

class Artist_ArtistCredit(Base):
    __tablename__ = 'artist_artist_credit'

    left_id = Column(BINARY(length=16), ForeignKey('artists.mbid_bin'))
    right_id = Column(Integer, ForeignKey('artist_credits.id'), primary_key=True)

    credit_name = Column(UnicodeText(collation='utf8_bin'))
    position = Column(SmallInteger(), primary_key=True, autoincrement=False)
    join_phrase = Column(UnicodeText(collation='utf8_bin'))

    child = relationship("ArtistCredit", backref="artist_assocs")

class Artist(Base):
    __tablename__ = 'artists'

    mbid_bin = Column(BINARY(length=16), primary_key=True)

    name = Column(UnicodeText(collation='utf8_bin'))
    last_cached = Column(DateTime, nullable = True)

    artist_credit_assocs = relationship("Artist_ArtistCredit", backref="artist")

    mbid = property(fget=mbid_get, fset=mbid_set)


class ArtistCredit(Base):
    __tablename__ = 'artist_credits'

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText(collation='utf8_bin'))
    picture_url = Column(UnicodeText(collation='utf8_bin'))
    user_set_picture = Column(Boolean)

    releases = relationship("Release", backref="artist_credit")
    recordings = relationship("Recording", backref="artist_credit")
    tracks = relationship("Track", backref="artist_credit")

class Recording(Base):
    __tablename__ = 'recordings'

    mbid_bin = Column(BINARY(length=16), primary_key=True)

    title = Column(UnicodeText(collation='utf8_bin'), nullable = True)
    waveplot_count = Column(Integer)
    last_cached = Column(DateTime, nullable = True)

    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'))

    tracks = relationship("Track", backref="recording")
    waveplots = relationship('WavePlot', backref='recording')



    def __init__(self, mbid):
        self.mbid = mbid
        self.waveplot_count = 0

    mbid = property(fget=mbid_get, fset=mbid_set)

class Release(Base):
    __tablename__ = 'releases'

    mbid_bin = Column(BINARY(length=16), primary_key=True)

    title = Column(UnicodeText(collation='utf8_bin'), nullable = True)
    dr_level = Column(SmallInteger, nullable = True)
    last_cached = Column(DateTime, nullable = True)

    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'), nullable = True)

    tracks = relationship("Track", backref="release")

    def __init__(self, mbid):
        self.mbid = mbid

    mbid = property(fget=mbid_get, fset=mbid_set)


class Track(Base):
    __tablename__ = 'tracks'

    mbid_bin = Column(BINARY(length=16), primary_key=True)

    title = Column(UnicodeText(collation='utf8_bin'), nullable = True)
    track_number = Column(SmallInteger)
    disc_number = Column(SmallInteger)

    dr_level = Column(SmallInteger, nullable = True)

    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'), nullable = True)
    release_mbid_bin = Column(BINARY(length=16), ForeignKey('releases.mbid_bin'))
    recording_mbid_bin = Column(BINARY(length=16), ForeignKey('recordings.mbid_bin'))

    waveplots = relationship('WavePlot', backref='track')

    last_cached = Column(DateTime, nullable = True)

    def __init__(self, mbid, track_number, disc_number, release, recording):
        self.mbid = mbid
        self.track_number = track_number
        self.disc_number = disc_number
        self.release_mbid_bin = release.mbid_bin
        self.recording_mbid_bin = recording.mbid_bin

    mbid = property(fget=mbid_get, fset=mbid_set)

class WavePlot(Base):
    __tablename__ = 'waveplots'

    uuid_bin = Column(BINARY(length=16), primary_key=True)

    length = Column(Interval)
    trimmed_length = Column(Interval)

    source_type = Column(String(20, collation='ascii_bin'))
    sample_rate = Column(Integer)
    bit_depth = Column(SmallInteger)
    bit_rate = Column(Integer)

    num_channels = Column(SmallInteger)
    dr_level = Column(SmallInteger)

    image_sha1 = Column(BINARY(length=20))
    thumbnail_bin = Column(BINARY(length=50))
    sonic_hash = Column(SmallInteger)

    version = Column(String(20, collation='ascii_bin'))
    submit_date = Column(DateTime)

    editor_id = Column(Integer, ForeignKey('editors.id'))
    track_mbid_bin = Column(BINARY(length=16), ForeignKey('tracks.mbid_bin'))
    recording_mbid_bin = Column(BINARY(length=16), ForeignKey('recordings.mbid_bin'))

    @property
    def uuid(self):
        return str(uuid.UUID(bytes=self.uuid_bin))

    @uuid.setter
    def uuid(self, value):
        self.uuid_bin = uuid.UUID(hex=value).bytes

    @property
    def thumbnail_b64(self):
        return base64.b64encode(self.thumbnail_bin)



def setup():
    engine = create_engine('mysql://{}:{}@{}/waveplot_alchemy'.format(passwords['mysql']['username'],passwords['mysql']['password'],passwords['mysql']['host']))

    Base.metadata.create_all(engine)

    Session.configure(bind=engine)

