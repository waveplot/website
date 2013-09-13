from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import Column, Integer, BigInteger, UnicodeText, Boolean, SmallInteger, BINARY, ForeignKey, Interval, String

import uuid
import base64

from passwords import passwords

Base = declarative_base()
Session = sessionmaker()

def mbid_get(self):
    return str(uuid.UUID(bytes=self.mbid_bin))

def mbid_set(self, value):
    self.mbid_bin = uuid.UUID(hex=value).bytes

class Editor(Base):
    __tablename__ = 'editors'

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText(collation='utf8_bin'))
    email = Column(UnicodeText(collation='utf8_bin'))
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

    artist_credit_assocs = relationship("Artist_ArtistCredit", backref="artist")

    mbid = property(fget=mbid_get, fset=mbid_set)


class ArtistCredit(Base):
    __tablename__ = 'artist_credits'

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText(collation='utf8_bin'))
    picture_url = Column(UnicodeText(collation='utf8_bin'))
    user_set_picture = Column(Boolean)

    releases = relationship("Release", backref="artist_credit")

class Recording(Base):
    __tablename__ = 'recordings'

    mbid_bin = Column(BINARY(length=16), primary_key=True)

    title = Column(UnicodeText(collation='utf8_bin'))
    waveplot_count = Column(Integer)

    tracks = relationship("Track", backref="recording")

    def __init__(self, mbid, title):
        self.mbid = mbid
        self.title = title
        self.waveplot_count = 0

    mbid = property(fget=mbid_get, fset=mbid_set)

class Release(Base):
    __tablename__ = 'releases'

    mbid_bin = Column(BINARY(length=16), primary_key=True)

    title = Column(UnicodeText(collation='utf8_bin'))

    artist_credit_id = Column(Integer, ForeignKey('artist_credits.id'))

    tracks = relationship("Track", backref="release")

    def __init__(self, mbid, title, artist_credit):
        self.mbid_bin = mbid
        self.title = title
        self.artist_credit_id = artist_credit

    mbid = property(fget=mbid_get, fset=mbid_set)


class Track(Base):
    __tablename__ = 'tracks'

    mbid_bin = Column(BINARY(length=16), primary_key=True)

    title = Column(UnicodeText(collation='utf8_bin'))
    track_number = Column(SmallInteger())
    disc_number = Column(SmallInteger())

    release_mbid_bin = Column(BINARY(length=16), ForeignKey('releases.mbid_bin'))
    recording_mbid_bin = Column(BINARY(length=16), ForeignKey('recordings.mbid_bin'))

    waveplots = relationship('WavePlot', backref='track')

    def __init__(self, mbid, title, track_number, disc_number, num_channels, release, recording):
        self.mbid_bin = mbid
        self.title = title
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
    audio_barcode = Column(SmallInteger)

    editor_id = Column(Integer, ForeignKey('editors.id'))
    track_mbid_bin = Column(BINARY(length=16), ForeignKey('tracks.mbid_bin'))

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

