#!/usr/bin/env python
# -*- coding: utf8 -*-

import os.path
import base64
import hashlib
import zlib

THUMB_IMAGE_WIDTH = 50
THUMB_IMAGE_HEIGHT = 21

PREVIEW_IMAGE_WIDTH = 400
PREVIEW_IMAGE_HEIGHT = 151

def waveplot_uuid_to_filename(uuid):
    return os.path.realpath(os.path.join("./waveplot/static/images/waveplots/", uuid[0:3], uuid[3:6], uuid[6:]))

def waveplot_uuid_to_url_suffix(uuid):
    return "images/waveplots/{}/{}/{}".format(uuid[0:3], uuid[3:6], uuid[6:])

class WavePlotImage():
    def __init__(self, encoded_data):
        self.raw_data = zlib.decompress(base64.b64decode(encoded_data))
        self.b64_data = base64.b64encode(self.raw_data)

        self.b64_thumb = None
        self.b64_preview = None

    def sha1_hex(self):
        m = hashlib.sha1(self.raw_data)
        return m.hexdigest()

    def _make_preview_image_(self):
        resample_factor = float(len(self.raw_data)) / PREVIEW_IMAGE_WIDTH;

        if resample_factor > 1.0:
            samples_weighting = resample_factor
            current_average = 0.0
            averages = []
            samples_remaining = int(samples_weighting + 0.999999)
            for value in self.raw_data:
                if samples_remaining == 1:
                    current_average += (ord(value) * samples_weighting)
                    averages.append(current_average / resample_factor)
                    current_average = (ord(value) * (1.0 - samples_weighting))
                    samples_weighting = resample_factor + samples_weighting - 1.0
                    samples_remaining = int(samples_weighting + 0.999999)
                else:
                    current_average += ord(value)
                    samples_remaining -= 1
                    samples_weighting -= 1.0
        else:
            averages = []
            for value in self.raw_data:
                averages.append(ord(value))

        data_str = ""

        for average in averages:
            data_str += chr(int(((average * 75) / 200) + 0.5))

        self.b64_preview = base64.b64encode(data_str)

    def _make_thumb_image_(self):
        resample_factor = float(len(self.raw_data)) / THUMB_IMAGE_WIDTH;

        if resample_factor > 1.0:
            samples_weighting = resample_factor
            current_average = 0.0
            averages = []
            samples_remaining = int(samples_weighting + 0.999999)
            for value in self.raw_data:
                if samples_remaining == 1:
                    current_average += (ord(value) * samples_weighting)
                    averages.append(current_average / resample_factor)
                    current_average = (ord(value) * (1.0 - samples_weighting))
                    samples_weighting = resample_factor + samples_weighting - 1.0
                    samples_remaining = int(samples_weighting + 0.999999)
                else:
                    current_average += ord(value)
                    samples_remaining -= 1
                    samples_weighting -= 1.0
        else:
            averages = []
            for value in self.raw_data:
                averages.append(ord(value))

        data_str = ""

        for average in averages:
            data_str += chr(int(((average * 10) / 200) + 0.5))

        self.b64_thumb = base64.b64encode(data_str)

    def generate_image_data(self):
        self._make_thumb_image_()
        self._make_preview_image_()

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
            img_file.write(self.b64_data)

        with open(self.filename_prefix + "_preview", "wb") as img_file:
            img_file.write(self.b64_preview)


