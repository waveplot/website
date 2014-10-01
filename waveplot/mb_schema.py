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

"""This module is extracted from mbws3 - it contains mappings for the musicbrainz
entities used by WavePlot.
"""

from __future__ import print_function, absolute_import, division

import base64
import datetime

from .schema import db
from sqlalchemy.dialects.postgresql import UUID

class Artist(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(UUID, unique=True, nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)
    sort_name = db.Column(db.UnicodeText, nullable=False)

    begin_date_year = db.Column(db.SmallInteger)
    begin_date_month = db.Column(db.SmallInteger)
    begin_date_day = db.Column(db.SmallInteger)

    end_date_year = db.Column(db.SmallInteger)
    end_date_month = db.Column(db.SmallInteger)
    end_date_day = db.Column(db.SmallInteger)

    type_id = db.Column('type', db.Integer, db.ForeignKey('musicbrainz.artist_type.id'))
    area_id = db.Column('area', db.Integer, db.ForeignKey('musicbrainz.area.id'))
    gender_id = db.Column('gender',db.Integer, db.ForeignKey('musicbrainz.gender.id'))
    comment = db.Column(db.Unicode(255), default=u'', nullable=False)

    edits_pending = db.Column(db.Integer, default=0, nullable=False)
    last_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    ended = db.Column(db.Boolean, default=False, nullable=False)

    begin_area_id = db.Column('begin_area',db.Integer, db.ForeignKey('musicbrainz.area.id'))
    end_area_id = db.Column('end_area',db.Integer, db.ForeignKey('musicbrainz.area.id'))

    type = db.relationship('ArtistType')
    gender = db.relationship('Gender')
    area = db.relationship('Area', foreign_keys=area_id)
    begin_area = db.relationship('Area', foreign_keys=begin_area_id)
    end_area = db.relationship('Area', foreign_keys=end_area_id)


class ArtistType(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)

    parent = db.Column(db.Integer, db.ForeignKey('musicbrainz.artist_type.id'))

    child_order = db.Column(db.Integer, default=0, nullable=False)

    description = db.Column(db.UnicodeText)

    children = db.relationship('ArtistType')


class Gender(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)

    parent = db.Column(db.Integer, db.ForeignKey('musicbrainz.gender.id'))

    child_order = db.Column(db.Integer, default=0, nullable=False)

    description = db.Column(db.UnicodeText)

    children = db.relationship('Gender')


class Area(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(UUID, unique=True, nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)

    type_id = db.Column('type', db.Integer, db.ForeignKey('musicbrainz.area_type.id'))

    edits_pending = db.Column(db.Integer, default=0, nullable=False)
    last_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    begin_date_year = db.Column(db.SmallInteger)
    begin_date_month = db.Column(db.SmallInteger)
    begin_date_day = db.Column(db.SmallInteger)

    end_date_year = db.Column(db.SmallInteger)
    end_date_month = db.Column(db.SmallInteger)
    end_date_day = db.Column(db.SmallInteger)

    ended = db.Column(db.Boolean, default=False, nullable=False)
    comment = db.Column(db.Unicode(255), default=u'', nullable=False)

    type = db.relationship('AreaType')


class AreaType(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)

    parent = db.Column(db.Integer, db.ForeignKey('musicbrainz.area_type.id'))

    child_order = db.Column(db.Integer, default=0, nullable=False)

    description = db.Column(db.UnicodeText)

    children = db.relationship('AreaType')


class Recording(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(UUID, unique=True, nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)

    artist_credit_id = db.Column('artist_credit', db.Integer, db.ForeignKey('musicbrainz.artist_credit.id'), nullable=False)

    length = db.Column(db.Integer)

    comment = db.Column(db.Unicode(255), default=u'', nullable=False)
    edits_pending = db.Column(db.Integer, default=0, nullable=False)

    last_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    video = db.Column(db.Boolean, default=False)

    artist_credit = db.relationship('ArtistCredit')


class ArtistCredit(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)

    artist_count = db.Column(db.SmallInteger, nullable=False)

    ref_count = db.Column(db.Integer, default=0)

    created = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)


class Release(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(UUID, unique=True, nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)

    artist_credit_id = db.Column('artist_credit', db.Integer, db.ForeignKey('musicbrainz.artist_credit.id'), nullable=False)
    release_group_id = db.Column('release_group', db.Integer, db.ForeignKey('musicbrainz.release_group.id'), nullable=False)
    status_id = db.Column('status', db.Integer, db.ForeignKey('musicbrainz.release_status.id'))
    packaging_id = db.Column('packaging', db.Integer, db.ForeignKey('musicbrainz.release_packaging.id'))
    language_id = db.Column('language', db.Integer, db.ForeignKey('musicbrainz.language.id'))
    script_id = db.Column('script', db.Integer, db.ForeignKey('musicbrainz.script.id'))

    barcode = db.Column(db.Unicode(255))
    comment = db.Column(db.Unicode(255), default=u'', nullable=False)

    edits_pending = db.Column(db.Integer, default=0, nullable=False)
    quality = db.Column(db.SmallInteger, default=-1, nullable=False)

    last_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    packaging = db.relationship('ReleasePackaging')
    status = db.relationship('ReleaseStatus')
    language = db.relationship('Language')
    artist_credit = db.relationship('ArtistCredit')
    release_group = db.relationship('ReleaseGroup', backref='releases')
    script = db.relationship('Script')


class ReleasePackaging(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)

    parent = db.Column(db.Integer, db.ForeignKey('musicbrainz.release_packaging.id'))

    child_order = db.Column(db.Integer, default=0, nullable=False)

    description = db.Column(db.UnicodeText)

    children = db.relationship('ReleasePackaging')


class ReleaseStatus(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)

    parent = db.Column(db.Integer, db.ForeignKey('musicbrainz.release_status.id'))

    child_order = db.Column(db.Integer, default=0, nullable=False)

    description = db.Column(db.UnicodeText)

    children = db.relationship('ReleaseStatus')


class Language(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)

    iso_code_2t = db.Column(db.Unicode(3))
    iso_code_2b = db.Column(db.Unicode(3))
    iso_code_1 = db.Column(db.Unicode(2))

    name = db.Column(db.Unicode(100), nullable=False)

    frequency = db.Column(db.Integer, default=0, nullable=False)

    iso_code_3 = db.Column(db.Unicode(2))


class Script(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)

    iso_code = db.Column(db.CHAR(4, convert_unicode=True), nullable=False)
    iso_number = db.Column(db.CHAR(3, convert_unicode=True), nullable=False)

    name = db.Column(db.Unicode(100), nullable=False)
    frequency = db.Column(db.Integer, default=0, nullable=False)


class ReleaseGroup(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(UUID, unique=True, nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)

    artist_credit_id = db.Column('artist_credit', db.Integer, db.ForeignKey('musicbrainz.artist_credit.id'), nullable=False)
    type_id = db.Column('type', db.Integer, db.ForeignKey('musicbrainz.release_group_primary_type.id'))

    comment = db.Column(db.Unicode(255), default=u'', nullable=False)

    edits_pending = db.Column(db.Integer, default=0, nullable=False)

    last_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    artist_credit = db.relationship('ArtistCredit')
    type = db.relationship('ReleaseGroupPrimaryType')


class ReleaseGroupPrimaryType(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)

    parent = db.Column(db.Integer, db.ForeignKey('musicbrainz.release_group_primary_type.id'))

    child_order = db.Column(db.Integer, default=0, nullable=False)

    description = db.Column(db.UnicodeText)

    children = db.relationship('ReleaseGroupPrimaryType')


class Medium(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)

    release_id = db.Column('release', db.Integer, db.ForeignKey('musicbrainz.release.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    format = db.Column(db.Integer)
    name = db.Column(db.Unicode(255))

    edits_pending = db.Column(db.Integer, default=0, nullable=False)
    last_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    track_count = db.Column(db.Integer, default=0, nullable=False)


class Track(db.Model):

    __table_args__ = {'schema':'musicbrainz'}

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(UUID, unique=True, nullable=False)

    recording_id = db.Column('recording', db.Integer, db.ForeignKey('musicbrainz.recording.id'), nullable=False)
    medium_id = db.Column('medium', db.Integer, db.ForeignKey('musicbrainz.medium.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    number = db.Column(db.UnicodeText, nullable=False)
    name = db.Column(db.Unicode, nullable=False)
    artist_credit_id = db.Column(db.Integer, db.ForeignKey('musicbrainz.artist_credit.id'), nullable=False)
    length = db.Column(db.Integer)

    edits_pending = db.Column(db.Integer, default=0, nullable=False)

    last_updated = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    artist_credit = db.relationship('ArtistCredit')
    recording = db.relationship('Recording')
