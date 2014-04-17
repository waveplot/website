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

from __future__ import print_function, absolute_import, division

from waveplot import manager

from waveplot.schema import db, Question


def post_get(result=None, **kw):
    question = db.session.query(Question).filter_by(id=result['id']).first()

    question.visits += 1

    db.session.commit()

def pre_post(data=None, **kw):
    # Get rid of any answer the user has tried to post, since only admin can answer questions
    data['answer'] = None
    data['answered'] = None


manager.create_api(Question, methods=['GET', 'POST'],
                   preprocessors={
                       'POST': [pre_post]
                   },
                   postprocessors={
                       'GET_SINGLE': [post_get]
                   })
