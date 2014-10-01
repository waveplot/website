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
import datetime

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .mb_schema import *
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from sqlalchemy.sql import text

WAVEPLOT_VERSIONS = [
    u"CITRUS",
    u"DAMSON",
]

class Edit(db.Model):
    """Respresents an Edit.

    An edit is any modification of WavePlot data by an Editor, whether that's
    uploading a new waveplot, adding tempo information to a track, or linking
    a WavePlot to various MusicBrainz entities.
    """

    __table_args__ = {'schema':'waveplot'}

    #Properties
    id = db.Column(db.Integer, primary_key=True)

    edit_time = db.Column(db.DateTime, nullable=False, default=text("(now() at time zone 'utc')"))
    edit_type = db.Column(db.SmallInteger, nullable=False)

    #Relationships
    editor_id = db.Column(db.Integer, db.ForeignKey('waveplot.editor.id'), nullable=False)
    waveplot_uuid = db.Column(UUID, db.ForeignKey('waveplot.waveplot.uuid'), nullable=False)

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

    __table_args__ = {'schema':'waveplot'}

    #Properties
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.UnicodeText, nullable=False)
    email = db.Column(db.UnicodeText, nullable=False)
    key = db.Column(db.BigInteger, nullable=False)

    queries_per_min = db.Column(db.Integer, nullable=False, server_default=text("60"))
    activated = db.Column(db.Boolean, nullable=False, default=False)

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


class WavePlotContext(db.Model):

    __tablename__ = 'waveplot_context'
    __table_args__ = {'schema':'waveplot'}

    id = db.Column(db.Integer, primary_key=True)

    waveplot_uuid = db.Column(UUID, db.ForeignKey('waveplot.waveplot.uuid'), nullable=False)

    release_id = db.Column(db.Integer, db.ForeignKey('musicbrainz.release.id'), nullable=False)
    recording_id = db.Column(db.Integer, db.ForeignKey('musicbrainz.recording.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('musicbrainz.track.id'), nullable=False)
    artist_credit_id = db.Column(db.Integer, db.ForeignKey('musicbrainz.artist_credit.id'), nullable=False)

    def __init__(self, waveplot_uuid, release_mbid = None,
                 recording_mbid = None, track_mbid = None):
        self.waveplot_uuid = waveplot_uuid
        self.release_mbid = release_mbid
        self.recording_mbid = recording_mbid
        self.track_mbid = track_mbid


class WavePlot(db.Model):
    """Class to represent a WavePlot, which is a representation of
    sound, and information related to that sound.
    """

    __tablename__ = 'waveplot'
    __table_args__ = {'schema':'waveplot'}

    uuid = db.Column(UUID, primary_key=True)

    length = db.Column(db.Interval, nullable=False)
    trimmed_length = db.Column(db.Interval, nullable=False)

    source_type = db.Column(db.String(20), nullable=False)
    sample_rate = db.Column(db.Integer)
    bit_depth = db.Column(db.SmallInteger)
    bit_rate = db.Column(db.Integer)

    num_channels = db.Column(db.SmallInteger, nullable=False)
    dr_level = db.Column(db.SmallInteger, nullable=False)

    image_hash = db.Column(BYTEA(length=20), nullable=False)
    full = db.Column(BYTEA, nullable=False)
    preview = db.Column(BYTEA(length=400), nullable=False)
    thumbnail = db.Column(BYTEA(length=50), nullable=False)
    sonic_hash = db.Column(db.Integer, nullable=False)

    version = db.Column(
        db.Enum(*WAVEPLOT_VERSIONS, name='waveplot_version',
                inherit_schema=True),
        nullable=False
    )

    contexts = db.relationship('WavePlotContext', backref="waveplot", passive_updates=False)

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

    __table_args__ = {'schema':'waveplot'}

    id = db.Column(db.Integer, primary_key=True)

    question = db.Column(db.UnicodeText, nullable=False)
    category = db.Column(db.SmallInteger, nullable=False)

    # Number of visits since "answered" date
    visits = db.Column(db.Integer, nullable=False, server_default=text("0"))

    # Optional properties
    answer = db.Column(db.UnicodeText, server_default=text("NULL"))
    answered = db.Column(db.DateTime, server_default=text("NULL"))

    def __init__(self, question, category, answer=None, answered=None,
                 visits=0):
        self.question = question
        self.category = category
        self.visits = visits
        self.answer = answer
        self.answered = answered

    def __repr__(self):
        return '<Question {!r}>'.format(self.question)
