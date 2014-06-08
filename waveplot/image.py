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

import os
import hashlib
import zlib
import datetime
import base64

THUMB_IMAGE_WIDTH = 50
THUMB_IMAGE_HEIGHT = 21

PREVIEW_IMAGE_WIDTH = 400
PREVIEW_IMAGE_HEIGHT = 151

def waveplot_uuid_to_filename(uuid):
    return os.path.realpath(os.path.join("./static/images/waveplots/", uuid[0:3], uuid[3:6], uuid[6:]))

def resample_data(data, target_length, source_amplitude, target_amplitude):
    # Calculate the number of data values per new data value
    resample_factor = len(data) / target_length

    # Check whether it's a down-sample
    if resample_factor > 1.0:
        new_data = []
        current_weighting = resample_factor
        current_value = 0.0

        for value in data:
            value = ord(value)

            current_value += value * min(current_weighting, 1.0)
            current_weighting -= 1.0

            # Negative, cap off previous value, make new
            if current_weighting <= 0.0:
                new_data.append(current_value / resample_factor)
                current_value = -value * current_weighting
                current_weighting += resample_factor
    else:
        new_data = [ord(value) for value in data]

    amplitude_factor = target_amplitude / source_amplitude

    return "".join(chr(int((v*amplitude_factor) + 0.5)) for v in new_data)

class WavePlotImage():
    def __init__(self, encoded_data):

        self.raw_data = zlib.decompress(base64.b64decode(encoded_data))

        self.sha1 = hashlib.sha1(self.raw_data)

        self.thumb_data = None
        self.preview_data = None
        self.sonic_hash = None

    def make_hash(self, start, end):
        image_data = self.raw_data[start:end+1]

        # Compute value, converting to ASCII '0' and '1' for int conversion.
        resampled_data = list(map(ord,resample_data(image_data, 16, 200, 200)))

        average = sum(resampled_data) / len(resampled_data)

        # '1' if value > average, otherwise '0'
        barcode_str = b"".join(
            ('1' if (x > average) else '0')
            for x in resampled_data
        )

        return int(barcode_str,2)

    def calculate_trimmed_length(self):
        min_val = 0
        for i, val in enumerate(self.raw_data):
            if ord(val) > 10:
                min_val = i
                break

        max_val = 0
        for i, val in enumerate(reversed(self.raw_data)):
            if ord(val) > 10:
                max_val = i
                break

        max_val = len(self.raw_data) - max_val
        self.trimmed_length = datetime.timedelta(seconds=int((max_val - min_val) / 4))

        return (min_val, max_val)

    def generate_image_data(self):
        self.thumb_data = resample_data(self.raw_data, THUMB_IMAGE_WIDTH, 200,
                                        int(THUMB_IMAGE_HEIGHT / 2))

        self.preview_data = resample_data(self.raw_data, PREVIEW_IMAGE_WIDTH,
                                          200, int(PREVIEW_IMAGE_HEIGHT / 2))

        min_val, max_val = self.calculate_trimmed_length()

        self.sonic_hash = self.make_hash(min_val, max_val)

    def save(self, uuid):
        self.filename_prefix = waveplot_uuid_to_filename(uuid)

        image_dir = os.path.dirname(self.filename_prefix)

        try:
            os.makedirs(image_dir)
        except OSError:
            pass

        if not os.path.exists(image_dir):
            return "Upload failed. Unable to store images."

        with open(self.filename_prefix, "wb") as img_file:
            img_file.write(self.raw_data)

        with open(self.filename_prefix + "_preview", "wb") as img_file:
            img_file.write(self.preview_data)


