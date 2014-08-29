
from flask.ext.testing import TestCase

from waveplot import create_app
from waveplot.schema import db, Editor, WavePlot
from waveplot.passwords import passwords

import json
import requests
import datetime

class MyTest(TestCase):

    config = {
        "SQLALCHEMY_DATABASE_URI":'mysql://{}:{}@{}/waveplot_testing'.format(passwords['mysql']['username'],passwords['mysql']['password'],passwords['mysql']['host']),
        "TESTING":True
    }

    def create_app(self):
        # pass in test configuration
        return create_app(self.config)

    def setUp(self):
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_pre_post_no_duplicate(self):
        from waveplot.json.waveplot import pre_post

        #Add editor
        e = Editor(name=u"TestEditor", email=u"editor@test.com", key=12345678, activated=True)
        db.session.add(e)
        db.session.commit()

        data = {
            "image":"eJxNkVtP0wAAhSU++MKLl6CMbe223tfb2nXr2q3drWs3doeNNQNBBogsDFwAN5U7EkiIYjSCJmiiRmLE+GjCiy/G+LMs0QfP20lOvpyT03P5Su+1m7YBB4gQJAGDTrslF8oIPEMSNMdzDEmSNE3RFEUzLEtRjJwxG3cquZSRL5aKtcbi4/WV1ni1cntxY39vvdt5sDw/MTJcLue1cEAISmE5FAryrBeB3C4QcIJuCPaAAOCGMQLHcQwjKEGOxpKD5uz9+cmxRntrZ3ncCNI4DGNMIKwqEk/ALghnA6LoZ7yoB3QCbgTHYLcLwrykBaAEKSIHBX9I1TLZfLGYNyI+FHQ6gYuAVZukWEFSlGhcz5UKhmLhYC8XUpSwyLFsMFkam2225kbzempwaCiX1tOFYjFnaDFZ9PNCUAyJwUDAz3Ec7/cxDCcqqqqoCSNjxCWOwiA3CFqjHA5rF4wgCIRgBElSvJQqVM1apTSoa4lkSs9ki9X6+N3piaoRkZV02azXhgppLRGPaZlCtV43a7XRyZnZ5kL3ydOTj58+vNzd2nv97cev3z/Pz1516zEahlCLa/3g43mOF9WkFlPjejafTqhKNKbKfpbxBcLxwmj74O3p+8OdtY2d7a29o9Pv519P9jvthwfvzr6cHG6uLMw0ZpqLrWmzkNa1uCKJgo9EPdYxTofTBSOwGwBcHgTDL64haF5OpHOZVCpr3msvTI2Uqo3WfGNYi0iSrOpl0yyoDAyC//KEF0c9HghBURRnBCksiUFRlKSQFApJcjiuV5sbz1/sPlpaXl3tLHU2nx0fHay15lrbx6ef3+x256bGqpURs1YyomFZsnrxPpYmvQRJUQQE2G0DNlv/LZsdcEMYxXIs4bH39924frUP9AYCxEDv5Z5Lf9Xzvyz/B7bSvls=",
            "editor":12345678,
            "length":183,
            "source_type":"AAC",
            "sample_rate":None,
            "bit_depth":None,
            "bit_rate":50516,
            "num_channels":2,
            "dr_level":14.3,
            "version":"CITRUS"
        }

        pre_post(data)

        #Test transformed data
        # These values should be unmodified
        self.assertEquals(data['version'], b'CITRUS')
        self.assertEquals(data['source_type'], b'AAC')
        self.assertEquals(data['bit_rate'], 50516)
        self.assertEquals(data['num_channels'], 2)

        #Times should be transformed from seconds to timedelta, and trimmed_length should have been calculated.
        self.assertEquals(data['length'], datetime.timedelta(seconds=183))
        self.assertEquals(data['trimmed_length'], datetime.timedelta(seconds=176))

        #DR Level should be multiplied by 10 for storage as an integer.
        self.assertEquals(data['dr_level'], 143)

        print(data)

    def test_pre_post_duplicate(self):
        from waveplot.json.waveplot import pre_post
        from flask.ext.restless import ProcessingException

        #Add editor
        e = Editor(name=u"TestEditor", email=u"editor@test.com", key=12345678, activated=True)
        db.session.add(e)
        db.session.commit()

        wp = WavePlot(
            u"0d70dabe-42b7-4982-ac1d-37aa0eaa3bbe",
            datetime.timedelta(seconds=183), datetime.timedelta(seconds=176),
            b'AAC', None, None, 50516, 2, 143,
            b"{\x12\xe92n\xf6\xc3Mx\xbf,\xf9\xfdQ\x18\\:5/'",
            b'\x01\x02\x02\x03\x05\x06\x03\x02\x02\x05\x03\x02\x02\x03\x03\x03\x03\x04\x04\x03\x03\x02\x02\x04\x04\x04\x04\x07\x05\x03\x03\x05\x07\x06\x03\x02\x02\x04\x04\x02\x02\x03\x06\x07\x04\x02\x02\x02\x01\x00',
            34, b'CITRUS')

        db.session.add(wp)
        db.session.commit()

        data = {
            "image":"eJxNkVtP0wAAhSU++MKLl6CMbe223tfb2nXr2q3drWs3doeNNQNBBogsDFwAN5U7EkiIYjSCJmiiRmLE+GjCiy/G+LMs0QfP20lOvpyT03P5Su+1m7YBB4gQJAGDTrslF8oIPEMSNMdzDEmSNE3RFEUzLEtRjJwxG3cquZSRL5aKtcbi4/WV1ni1cntxY39vvdt5sDw/MTJcLue1cEAISmE5FAryrBeB3C4QcIJuCPaAAOCGMQLHcQwjKEGOxpKD5uz9+cmxRntrZ3ncCNI4DGNMIKwqEk/ALghnA6LoZ7yoB3QCbgTHYLcLwrykBaAEKSIHBX9I1TLZfLGYNyI+FHQ6gYuAVZukWEFSlGhcz5UKhmLhYC8XUpSwyLFsMFkam2225kbzempwaCiX1tOFYjFnaDFZ9PNCUAyJwUDAz3Ec7/cxDCcqqqqoCSNjxCWOwiA3CFqjHA5rF4wgCIRgBElSvJQqVM1apTSoa4lkSs9ki9X6+N3piaoRkZV02azXhgppLRGPaZlCtV43a7XRyZnZ5kL3ydOTj58+vNzd2nv97cev3z/Pz1516zEahlCLa/3g43mOF9WkFlPjejafTqhKNKbKfpbxBcLxwmj74O3p+8OdtY2d7a29o9Pv519P9jvthwfvzr6cHG6uLMw0ZpqLrWmzkNa1uCKJgo9EPdYxTofTBSOwGwBcHgTDL64haF5OpHOZVCpr3msvTI2Uqo3WfGNYi0iSrOpl0yyoDAyC//KEF0c9HghBURRnBCksiUFRlKSQFApJcjiuV5sbz1/sPlpaXl3tLHU2nx0fHay15lrbx6ef3+x256bGqpURs1YyomFZsnrxPpYmvQRJUQQE2G0DNlv/LZsdcEMYxXIs4bH39924frUP9AYCxEDv5Z5Lf9Xzvyz/B7bSvls=",
            "editor":12345678,
            "length":183,
            "source_type":"AAC",
            "sample_rate":None,
            "bit_depth":None,
            "bit_rate":50516,
            "num_channels":2,
            "dr_level":14.3,
            "version":"CITRUS"
        }

        self.assertRaises(ProcessingException, pre_post, data)

        print(data)
