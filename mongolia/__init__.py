"""
The MIT License (MIT)

Copyright (c) 2014 Zagaran, Inc.

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

from mongolia.mongo_connection import (connect_to_database, authenticate_connection,
    set_defaults_handling, AlertLevel, add_user, list_database, set_type_checking,
    add_superuser, set_test_mode, drop_test_database)
from mongolia.constants import ID_KEY, REQUIRED, UPDATE, CHILD_TEMPLATE
from mongolia.database_object import DatabaseObject
from mongolia.database_collection import DatabaseCollection
from mongolia.testing import MongoliaTestCase

__all__ = (
           "connect_to_database",
           "authenticate_connection",
           "set_defaults_handling",
           "set_type_checking",
           "add_user",
           "add_superuser",
           "list_database",
           "AlertLevel",
           "ID_KEY",
           "REQUIRED",
           "UPDATE",
           "CHILD_TEMPLATE",
           "DatabaseObject",
           "DatabaseCollection",
           "set_test_mode",
           "drop_test_database",
           "MongoliaTestCase"
           )
