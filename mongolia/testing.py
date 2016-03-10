"""
The MIT License (MIT)

Copyright (c) 2015 Zagaran, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

@author: Zags (Benjamin Zagorsky)
"""

import unittest2
import sys
from mongolia.mongo_connection import set_test_mode, drop_test_database

class MongoliaTestCase(unittest2.TestCase):
    """ Child class of untitest.TestCase that does the following:
            * Sets the Mongolia connection to test mode before starting
            * Sets the Mongolia connection out of test mode after finishing
            * Drops the test database after each test
        The result of this is that each test case will run on a mongo database
        containing only what the setUp method and the test case itself have
        created.
    """
    
    @classmethod
    def setUpClass(cls):
        set_test_mode(True)
        super(MongoliaTestCase, cls).setUpClass()
    
    @classmethod
    def tearDownClass(cls):
        set_test_mode(False)
        super(MongoliaTestCase, cls).tearDownClass()
    
    def __call__(self, result=None):
        """ Adds extra setup and teardown by overriding the __call__ method
            so that children of this class can define setUp and tearDown
            without needing to call the corresonding super methods """
        try:
            self._mongolia_test_setup()
        except Exception:
            result.addError(self, sys.exc_info())
            return
        super(MongoliaTestCase, self).__call__(result)
        try:
            self._mongolia_test_teardown()
        except Exception:
            result.addError(self, sys.exc_info())
            return
    
    def _mongolia_test_setup(self):
        set_test_mode(True)
    
    def _mongolia_test_teardown(self):
        drop_test_database()
