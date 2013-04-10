#!/usr/bin/env python
# -*- coding: utf8 -*-

import os.path
import base64

THUMB_IMAGE_WIDTH = 50
THUMB_IMAGE_HEIGHT = 21

PREVIEW_IMAGE_WIDTH = 400
PREVIEW_IMAGE_HEIGHT = 151

def waveplot_uuid_to_filename( uuid ):
    return os.path.realpath( os.path.join( "./waveplot/static/images/waveplots/", uuid[0:3], uuid[3:6], uuid[6:] ) )

def waveplot_uuid_to_url_suffix( uuid ):
    return "images/waveplots/{}/{}/{}".format( uuid[0:3], uuid[3:6], uuid[6:] )

class WavePlot():
    def __init__( self, b64_data, uuid ):
        self.b64_data = b64_data
        self.data = base64.b64decode( b64_data )

        self.uuid = uuid

        self.filename_prefix = waveplot_uuid_to_filename( self.uuid )

        self.b64_thumb = None
        self.b64_preview = None

    def _make_preview_image_( self ):
        resample_factor = float( len( self.data ) ) / PREVIEW_IMAGE_WIDTH;

        if resample_factor > 1.0:
            samples_weighting = resample_factor
            current_average = 0.0
            averages = []
            samples_remaining = int( samples_weighting + 0.999999 )
            for value in self.data:
                if samples_remaining == 1:
                    current_average += ( ord( value ) * samples_weighting )
                    averages.append( current_average / resample_factor )
                    current_average = ( ord( value ) * ( 1.0 - samples_weighting ) )
                    samples_weighting = resample_factor + samples_weighting - 1.0
                    samples_remaining = int( samples_weighting + 0.999999 )
                else:
                    current_average += ord( value )
                    samples_remaining -= 1
                    samples_weighting -= 1.0
        else:
            averages = []
            for value in self.data:
                averages.append( ord( value ) )

        data_str = ""

        for average in averages:
            data_str += chr( int( ( ( average * 75 ) / 200 ) + 0.5 ) )

        for char in data_str:
            print str( ord( char ) ) + ","

        self.b64_preview = base64.b64encode( data_str )

    def _make_thumb_image_( self ):
        resample_factor = float( len( self.data ) ) / THUMB_IMAGE_WIDTH;

        if resample_factor > 1.0:
            samples_weighting = resample_factor
            current_average = 0.0
            averages = []
            samples_remaining = int( samples_weighting + 0.999999 )
            for value in self.data:
                if samples_remaining == 1:
                    current_average += ( ord( value ) * samples_weighting )
                    averages.append( current_average / resample_factor )
                    current_average = ( ord( value ) * ( 1.0 - samples_weighting ) )
                    samples_weighting = resample_factor + samples_weighting - 1.0
                    samples_remaining = int( samples_weighting + 0.999999 )
                else:
                    current_average += ord( value )
                    samples_remaining -= 1
                    samples_weighting -= 1.0
        else:
            averages = []
            for value in self.data:
                averages.append( ord( value ) )

        data_str = ""

        for average in averages:
            data_str += chr( int( ( ( average * 10 ) / 200 ) + 0.5 ) )

        self.b64_thumb = base64.b64encode( data_str )

    def generate_image_data( self ):
        self._make_thumb_image_()
        self._make_preview_image_()

    def save( self ):
        image_dir = os.path.dirname( self.filename_prefix )

        try:
            os.makedirs( image_dir )
        except OSError:
            pass

        if not os.path.exists( image_dir ):
            return "Upload failed. Unable to store images."

        with open( self.filename_prefix, "wb" ) as img_file:
            img_file.write( self.b64_data )

        with open( self.filename_prefix + "_preview", "wb" ) as img_file:
            print self.b64_preview
            img_file.write( self.b64_preview )

        with open( self.filename_prefix + "_thumb", "wb" ) as img_file:
            img_file.write( self.b64_thumb )


