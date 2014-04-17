#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover("tests")
    unittest.TextTestRunner(verbosity=2).run(suite)
