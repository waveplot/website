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
from sqlalchemy.ext.hybrid import hybrid_property

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

class Edit(Base):
    __tablename__ = 'edits'

    id = Column(Integer, primary_key=True)

    editor_id = Column(Integer, ForeignKey('editors.id'))
    waveplot_uuid_bin = Column(BINARY(length=16), ForeignKey('waveplots.uuid_bin'))
    
    edit_time = Column(DateTime)
    edit_type = Column(SmallInteger)

    waveplot = relationship("WavePlot", backref="edits")

class Editor(Base):
    __tablename__ = 'editors'

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText(collation='utf8_bin'))
    email = Column(UnicodeText(collation='utf8_bin'))
    queries_per_min = Column(Integer, default=60)
    key = Column(BigInteger)
    activated = Column(Boolean)

    edits = relationship("Edit", backref='editor')

    def __init__(self, name, email, key, activated = False):
        self.name = name
        self.email = email
        self.key = key
        self.activated = activated

class Artist_ArtistCredit(Base):
    __tablename__ = 'artist_artist_credit'

    artist_mbid = Column(BINARY(length=16), ForeignKey('artists.mbid_bin'))
    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'), primary_key=True)

    credit_name = Column(UnicodeText(collation='utf8_bin'))
    position = Column(SmallInteger(), primary_key=True, autoincrement=False)
    join_phrase = Column(UnicodeText(collation='utf8_bin'))

    artist_credit = relationship("ArtistCredit", backref="artist_assocs")

class Artist(Base):
    __tablename__ = 'artists'

    # Cached data
    mbid_bin = Column(BINARY(length=16), primary_key=True)
    name = Column(UnicodeText(collation='utf8_bin'))
    last_cached = Column(DateTime, nullable = True)

    # Data derived from relationships
    artist_credit_assocs = relationship("Artist_ArtistCredit", backref="artist", passive_updates=False)

    mbid = property(fget=mbid_get, fset=mbid_set)

    def __init__(self, mbid):
        self.mbid = mbid

class ArtistCredit(Base):
    __tablename__ = 'artist_credits'

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText(collation='utf8_bin'))
    picture_url = Column(UnicodeText(collation='utf8_bin'))
    user_set_picture = Column(Boolean)

    releases = relationship("Release", backref="artist_credit")
    recordings = relationship("Recording", backref="artist_credit")
    tracks = relationship("Track", backref="artist_credit")

    def __init__(self, name):
        self.name = name
        self.picture_url = u""
        self.user_set_picture = False

class Recording(Base):
    __tablename__ = 'recordings'

    # Cached items
    mbid_bin = Column(BINARY(length=16), primary_key=True) # Cache
    title = Column(UnicodeText(collation='utf8_bin')) # Cache
    last_cached = Column(DateTime, nullable = True) # Cache

    # Data derived from relationships
    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'))
    tracks = relationship("Track", backref="recording", passive_updates=False)
    waveplots = relationship('WavePlot', passive_updates=False)

    def __init__(self, mbid):
        self.mbid = mbid

    def cache(self, recording_data):
        self.mbid = recording_data['id']
        self.title = recording_data['title']
        self.last_cached = datetime.datetime.utcnow()

    mbid = property(fget=mbid_get, fset=mbid_set)

class Release(Base):
    __tablename__ = 'releases'

    # Cached items
    mbid_bin = Column(BINARY(length=16), primary_key=True) # Cache
    title = Column(UnicodeText(collation='utf8_bin')) # Cache
    last_cached = Column(DateTime, nullable = True) # Cache

    # Data derived from relationships
    dr_level = Column(SmallInteger, nullable = True)
    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'))
    tracks = relationship("Track", backref="release", passive_updates=False)

    def __init__(self, mbid):
        self.mbid = mbid

    def cache(self, release_data):
        self.mbid = release_data['id']
        self.title = release_data['title']
        self.last_cached = datetime.datetime.utcnow()

    # Calculate DR. DR should be stored as int with last digit after dp.
    def calculate_dr(self):
        num_tracks = len(self.tracks)
        if num_tracks > 0:
            average = 0.0
            for t in self.tracks:
                t.calculate_dr()
                average += t.dr_level

            self.dr_level = int(average / num_tracks)

    mbid = property(fget=mbid_get, fset=mbid_set)


class Track(Base):
    __tablename__ = 'tracks'

    # Fixed data
    mbid_bin = Column(BINARY(length=16), primary_key=True)
    track_number = Column(SmallInteger)
    disc_number = Column(SmallInteger)
    tempo = Column(SmallInteger, nullable = True)

    # Cached data
    title = Column(UnicodeText(collation='utf8_bin'))
    last_cached = Column(DateTime, nullable = True)

    # Derived data
    dr_level = Column(SmallInteger, nullable = True)
    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'))
    release_mbid_bin = Column(BINARY(length=16), ForeignKey('releases.mbid_bin'))
    recording_mbid_bin = Column(BINARY(length=16), ForeignKey('recordings.mbid_bin'))

    waveplots = relationship('WavePlot', backref='track', passive_updates=False)

    def __init__(self, mbid, track_number, disc_number, release, recording):
        self.mbid = mbid
        self.track_number = track_number
        self.disc_number = disc_number
        self.release_mbid_bin = release.mbid_bin
        self.recording_mbid_bin = recording.mbid_bin

    def cache(self, track_data):
        self.title = track_data['title']
        self.last_cached = datetime.datetime.utcnow()

    # Calculate DR. DR should be stored as int with last digit after dp.
    def calculate_dr(self):
        num_waveplots = len(self.waveplots)
        if num_waveplots > 0:
            average = 0.0
            for wp in self.waveplots:
                average += wp.dr_level

            self.dr_level = int(average / num_waveplots)

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
    sonic_hash = Column(Integer)

    version = Column(String(20, collation='ascii_bin'))

    track_mbid_bin = Column(BINARY(length=16), ForeignKey('tracks.mbid_bin'), nullable=True)
    recording_mbid_bin = Column(BINARY(length=16), ForeignKey('recordings.mbid_bin'), nullable=True)

    @property
    def uuid(self):
        return str(uuid.UUID(bytes=self.uuid_bin))

    @uuid.setter
    def uuid(self, value):
        self.uuid_bin = uuid.UUID(hex=value).bytes

    @property
    def thumbnail_b64(self):
        return base64.b64encode(self.thumbnail_bin)

class WavePlotContext(Base):
    __tablename__ = 'waveplotcontexts'

    uuid_bin = Column(BINARY(length=16), ForeignKey('waveplots.uuid_bin'), primary_key=True)

    track_number = Column(SmallInteger, nullable = True)
    disc_number = Column(SmallInteger, nullable = True)

    release_mbid_bin = Column(BINARY(length=16), nullable=True)
    recording_mbid_bin = Column(BINARY(length=16), nullable=True)
    track_mbid_bin = Column(BINARY(length=16), nullable=True)

    def __init__(self, uuid_bin):
        self.uuid = uuid_bin

    @property
    def uuid(self):
        return str(uuid.UUID(bytes=self.uuid_bin))

    @uuid.setter
    def uuid(self, value):
        self.uuid_bin = uuid.UUID(hex=value).bytes

# Class to model the questions/answers on the help page - not part of core data
class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    
    question = Column(UnicodeText(collation='utf8_bin'))
    answer = Column(UnicodeText(collation='utf8_bin'), nullable = True)
    
    answered = Column(DateTime, nullable = True)
    
    category = Column(SmallInteger)
    
    # Number of visits since "answered" date
    visits = Column(Integer)


def setup():
    engine = create_engine('mysql://{}:{}@{}/waveplot_alchemy'.format(passwords['mysql']['username'],passwords['mysql']['password'],passwords['mysql']['host']), pool_recycle = 14400)

    Base.metadata.create_all(engine)

    Session.configure(bind=engine)

