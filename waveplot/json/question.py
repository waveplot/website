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

import json

from flask import request, make_response

import waveplot.utils

from waveplot import app

from waveplot.schema import Session, Question

@app.route('/json/question', methods = ['GET'])
@waveplot.utils.crossdomain(origin = '*')
def question_all():
    session = Session()

    questions = session.query(Question)

    data = [
        {
            'id':q.id,
            'question':q.question,
            'visits':q.visits,
            'category':q.category,
            'answered':(q.answered.isoformat() if q.answered is not None else False),
            'url':None
        } for q in questions.all()
    ]

    session.close()

    return make_response(json.dumps(data))
    
@app.route('/json/question/<id>', methods = ['GET'])
@waveplot.utils.crossdomain(origin = '*')
def question_get(id):
    session = Session()

    q = session.query(Question).filter_by(id=id).first()

    data = {
        'id':q.id,
        'question':q.question,
        'answer':q.answer,
        'visits':q.visits,
        'category':q.category,
        'answered':(q.answered.isoformat() if q.answered is not None else False),
        'url':None
    }
    
    # Increment visit count
    q.visits += 1
    
    session.commit()
    session.close()

    return make_response(json.dumps(data))
