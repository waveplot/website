# -*- coding: utf8 -*-

# Copyright 2013, 2014 Ben Ockmore

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

"""This module describes the database schema of WavePlot, and sets up the
objects to be used by the SQLAlchemy-based ORM.

The following objects are defined:
 * Artist
 * ArtistArtistCredit
 * ArtistCredit
 * Edit
 * Editor
 * Release
 * Recording
 * Track
 * WavePlot
 * Question
"""

from __future__ import print_function, absolute_import, division

import base64

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()



TRACK_WAVEPLOT = db.Table(
    'track_waveplot',
    db.Column('track_mbid', db.Unicode(32, collation='utf8_bin'),
              db.ForeignKey('track.mbid')),
    db.Column('waveplot_uuid', db.Unicode(32, collation='utf8_bin'),
              db.ForeignKey('waveplot.uuid'))
)


class Artist(db.Model):
    """Represents an artist - someone who records music.

    An artist can have many artist credits, which feature on tracks,
    recordings and releases.
    """

    mbid = db.Column(db.Unicode(32, collation='utf8_bin'), primary_key=True)

    name = db.Column(db.UnicodeText(collation='utf8_bin'))
    last_cached = db.Column(db.DateTime)

    # Data derived from relationships
    artist_credit_assocs = db.relationship("ArtistArtistCredit", backref="artist", passive_updates=False)

    def __init__(self, mbid, name):
        self.mbid = mbid
        self.name = name

    def __repr__(self):
        return "<Artist {!r}>".format(self.name)


class ArtistArtistCredit(db.Model):
    """A class to link artists to their artist credits.

    Also enables artist credit names to be regenerated when one of the
    individual credits changes.
    """

    id = db.Column(db.Integer, primary_key=True)

    credit_name = db.Column(db.UnicodeText(collation='utf8_bin'))
    join_phrase = db.Column(db.UnicodeText(collation='utf8_bin'))

    position = db.Column(db.SmallInteger())

    artist_credit_id = db.Column(db.Integer, db.ForeignKey('artist_credit.id'))
    artist_mbid = db.Column(db.Unicode(32, collation='utf8_bin'),
                            db.ForeignKey('artist.mbid'))

    artist_credit = db.relationship("ArtistCredit", backref="artist_assocs")

    db.UniqueConstraint(position, artist_credit_id)

    def __init__(self, credit_name, join_phrase, position, artist_credit_id,
                 artist_mbid):
        self.credit_name = credit_name
        self.join_phrase = join_phrase
        self.position = position
        self.artist_credit_id = artist_credit_id
        self.artist_mbid = artist_mbid

    def __repr__(self):
        return (
            '<ArtistArtistCredit'
            '{!r} in {!r}>'.format(self.credit_name, self.artist_credit_id)
        )


class ArtistCredit(db.Model):
    """An artist credit - the way in which an artist is credited on a
    track, recording or release.
    """

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.UnicodeText(collation='utf8_bin'))

    # Relationships
    releases = db.relationship("Release", backref="artist_credit")
    recordings = db.relationship("Recording", backref="artist_credit")
    tracks = db.relationship("Track", backref="artist_credit")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Artist Credit {!r}>'.format(self.name)


class Edit(db.Model):
    """Respresents an Edit.

    An edit is any modification of WavePlot data by an Editor, whether that's
    uploading a new waveplot, adding tempo information to a track, or linking
    a WavePlot to various MusicBrainz entities.
    """

    #Properties
    id = db.Column(db.Integer, primary_key=True)

    edit_time = db.Column(db.DateTime)
    edit_type = db.Column(db.SmallInteger)

    #Relationships
    editor_id = db.Column(db.Integer, db.ForeignKey('editor.id'))
    waveplot_uuid = db.Column(db.Unicode(32, collation='utf8_bin'),
                              db.ForeignKey('waveplot.uuid'))

    waveplot = db.relationship("WavePlot", backref="edits")

    def __init__(self, edit_time, edit_type, editor_id, waveplot_uuid):
        self.edit_time = edit_time
        self.edit_type = edit_type
        self.editor_id = editor_id
        self.waveplot_uuid = waveplot_uuid

    def __repr__(self):
        return '<Edit {!r} at {!r}>'.format(self.edit_type, self.edit_time)


class Editor(db.Model):
    """Represents an Editor.

    An editor is a user of the WavePlot website who is able to
    contribute new WavePlots, by scanning audio files on their system.
    Contributors must be editors so that their contributions can be
    undone if made maliciously.
    """

    #Properties
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.UnicodeText(collation='utf8_bin'))
    email = db.Column(db.UnicodeText(collation='utf8_bin'))
    key = db.Column(db.BigInteger)

    queries_per_min = db.Column(db.Integer, default=60)
    activated = db.Column(db.Boolean, default=False)

    #Relationships
    edits = db.relationship("Edit", backref='editor')

    def __init__(self, name, email, key, queries_per_min=60, activated=False):
        self.name = name
        self.email = email
        self.key = key
        self.queries_per_min = queries_per_min
        self.activated = activated

    def __repr__(self):
        return '<Editor {!r}>'.format(self.name)


class Release(db.Model):
    """A release, which is a physically unique version of an album,
    single, or other product. Contains tracks, which are related
    to recordings.
    """

    mbid = db.Column(db.Unicode(32, collation='utf8_bin'), primary_key=True)

    title = db.Column(db.UnicodeText(collation='utf8_bin'), nullable=True, default=None)
    last_cached = db.Column(db.DateTime, nullable=True, default=None)

    # Data derived from relationships
    dr_level = db.Column(db.SmallInteger, nullable=True, default=None)

    artist_credit_id = db.Column(db.Integer, db.ForeignKey('artist_credit.id'), nullable=True, default=None)
    tracks = db.relationship("Track", backref="release", passive_updates=False)

    def __init__(self, mbid):
        self.mbid = mbid

    def __repr__(self):
        return "<Release {!r}>".format(self.title)

    # Calculate DR. DR should be stored as int with last digit after dp.
    def calculate_dr(self):
        """Calculate the DR level for the release, based on the average DR
        level of its tracks.
        """

        average = reduce(lambda x, y: x + y.dr_level, self.tracks, 0.0)
        num_tracks = len(self.tracks)

        if num_tracks == 0:
            self.dr_level = 0
        else:
            self.dr_level = int(average / num_tracks)


class Recording(db.Model):
    """A recording, which corresponds to the concept of a recording
    in MusicBrainz. Can have many tracks, and can be linked to many
    releases.
    """

    #Properties
    mbid = db.Column(db.Unicode(32, collation='utf8_bin'), primary_key=True)

    title = db.Column(db.UnicodeText(collation='utf8_bin'), nullable=True, default=None)
    last_cached = db.Column(db.DateTime, nullable=True, default=None)

    # Relationships
    artist_credit_id = db.Column(db.Integer, db.ForeignKey('artist_credit.id'), nullable=True, default=None)
    tracks = db.relationship("Track", backref="recording", passive_updates=False)

    def __init__(self, mbid):
        self.mbid = mbid

    def __repr__(self):
        return "<Recording {!r}>".format(self.title)


class Track(db.Model):
    """A track is a defined segment of a release, which features some
    audio.

    In theory, tracks should have a one-to-one or many-to-one
    relationship with WavePlots, but this might not be the case.
    """

    mbid = db.Column(db.Unicode(32, collation='utf8_bin'), primary_key=True)
    track_number = db.Column(db.SmallInteger)
    disc_number = db.Column(db.SmallInteger)

    # Cached data
    title = db.Column(db.UnicodeText(collation='utf8_bin'))
    last_cached = db.Column(db.DateTime)

    # Optional Info
    bpm = db.Column(db.SmallInteger, nullable=True)
    dr_level = db.Column(db.SmallInteger, nullable=True)

    # Derived data
    artist_credit_id = db.Column(db.Integer, db.ForeignKey('artist_credit.id'))
    release_mbid = db.Column(db.Unicode(32, collation='utf8_bin'), db.ForeignKey('release.mbid'))
    recording_mbid = db.Column(db.Unicode(32, collation='utf8_bin'), db.ForeignKey('recording.mbid'))

    waveplots = db.relationship('WavePlot', secondary=TRACK_WAVEPLOT,
                                backref=db.backref('tracks'), passive_updates=False)

    def __init__(self, mbid, track_number, disc_number, release, recording):
        self.mbid = mbid
        self.track_number = track_number
        self.disc_number = disc_number
        self.release_mbid_bin = release.mbid_bin
        self.recording_mbid_bin = recording.mbid_bin

    def __repr__(self):
        return "<Track {!r}>".format(self.title)

    # Calculate DR. DR should be stored as int with last digit after dp.
    def calculate_dr(self):
        """Calculate the DR level for the track, based on the average DR
        level of waveplots.
        """

        average = reduce(lambda x, y: x + y.dr_level, self.waveplots, 0.0)
        num_waveplots = len(self.waveplots)

        if num_waveplots == 0:
            self.dr_level = 0
        else:
            self.dr_level = int(average / num_waveplots)


class WavePlot(db.Model):
    """Class to represent a WavePlot, which is a representation of
    sound, and information related to that sound.
    """

    __tablename__ = 'waveplot'

    uuid = db.Column(db.Unicode(32, collation='utf8_bin'), primary_key=True)

    length = db.Column(db.Interval)
    trimmed_length = db.Column(db.Interval)

    source_type = db.Column(db.String(20, collation='ascii_bin'))
    sample_rate = db.Column(db.Integer)
    bit_depth = db.Column(db.SmallInteger)
    bit_rate = db.Column(db.Integer)

    num_channels = db.Column(db.SmallInteger)
    dr_level = db.Column(db.SmallInteger)

    image_sha1 = db.Column(db.BINARY(length=20))
    thumbnail = db.Column(db.BINARY(length=50))
    sonic_hash = db.Column(db.Integer)

    version = db.Column(db.String(20, collation='ascii_bin'))

    def __init__(self, uuid, length, trimmed_length, source_type, sample_rate,
                 bit_depth, bit_rate, num_channels, dr_level, image_sha1,
                 thumbnail, sonic_hash, version):
        self.uuid = uuid
        self.length = length
        self.trimmed_length = trimmed_length
        self.source_type = source_type
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.bit_rate = bit_rate
        self.num_channels = num_channels
        self.dr_level = dr_level
        self.image_sha1 = image_sha1
        self.thumbnail = thumbnail
        self.sonic_hash = sonic_hash
        self.version = version

    def __repr__(self):
        return '<WavePlot {!r}>'.format(self.uuid)

    @property
    def thumbnail_b64(self):
        """Get the thumbnail image as base64-encoded binary data."""
        return base64.b64encode(self.thumbnail_bin)


# Class to model the questions/answers on the help page - not part of core data
class Question(db.Model):
    """Class to represent questions on the website help page.
    """

    id = db.Column(db.Integer, primary_key=True)

    question = db.Column(db.UnicodeText(collation='utf8_bin'))
    category = db.Column(db.SmallInteger)

    # Number of visits since "answered" date
    visits = db.Column(db.Integer, default=0)

    # Optional properties
    answer = db.Column(db.UnicodeText(collation='utf8_bin'), nullable=True,
                       default=None)
    answered = db.Column(db.DateTime, nullable=True, default=None)

    def __init__(self, question, category, answer=None, answered=None,
                 visits=0):
        self.question = question
        self.category = category
        self.visits = visits
        self.answer = answer
        self.answered = answered

    def __repr__(self):
        return '<Question {!r}>'.format(self.question)
