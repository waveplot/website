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

import random

from flask.ext.restless import ProcessingException

from waveplot import manager, db
from waveplot.schema import Editor
from waveplot.utils import SendEmail

ACTIVATION_EMAIL_BODY = """
<p>Hi {}!</p>

<p>Please activate your WavePlot account using the activation link below:</p>

<p><a href="{}">{}</a></p>

<p>Many thanks for your help in building the WavePlot database!</p>
"""


def pre_post(data=None, **kw):
    email = data.get('email', '')

    at_pos = email.rfind('@')
    dot_pos = email.rfind('.')

    if ((at_pos < 1) or (dot_pos < (at_pos + 2)) or
            ((dot_pos + 2) >= len(email))):
        raise ProcessingException(message='Bad Email Address', status_code=400)

    if db.session.query(Editor).filter_by(email=email).first() is not None:
        raise ProcessingException(message='Email Address Already Registered',
                                  status_code=403)

    generated_key = random.randint(0, 999999999)
    while db.session.query(Editor).filter_by(key=generated_key).count():
        generated_key = random.randint(0, 999999999)

    data['key'] = generated_key


def post_post(result=None, **kw):
    # Send an activation email
    activation_url = "http://localhost/activate/"+str(result['key'])
    SendEmail(result['email'], "WavePlot Activation Required!",
              ACTIVATION_EMAIL_BODY.format(result['name'], activation_url,
                                           activation_url))


def pre_put(instance_id=None, data=None, **kw):
    # The activation key must be present and correct to make any changes here.
    instance = db.session.query(Editor).filter_by(id=instance_id).first()

    if instance is None:
        raise ProcessingException(message='Editor Does Not Exist',
                                  status_code=404)

    if data.get('key', None) != instance.key:
        raise ProcessingException(message='Incorrect Editor PIN',
                                  status_code=401)


manager.create_api(Editor, methods=['GET', 'POST', 'PUT'],
                   preprocessors={
                       'POST': [pre_post],
                       'PUT_SINGLE': [pre_put]
                   }, postprocessors={
                       'POST': [post_post]
                   })
