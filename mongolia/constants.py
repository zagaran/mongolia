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
from bson import ObjectId
from datetime import datetime

""" Special key required by mongo for all DatabaseObjects; uniquely
    identifies DatabaseObjects """
ID_KEY = "_id"

""" Not used in current library version """
INC = "$inc"

""" Greater than argument to mongo query """
GT = "$gt"

""" Set argument for mongo update """
SET = "$set"

""" List of types to check for under Connection.type_checking """
TYPES_TO_CHECK = [basestring, int, float, list, dict]

""" Indicates that a key in DatabaseObject.DEFAULTS is required """
REQUIRED = "__required__"

""" Special values for keys in DatabaseObject.DEFAULTS that are treated the same
    as REQUIRED, but are also contain type information for type checking.
    A key that has a REQUIRED_TYPE will raise an error if the wrong type of
    data is set for that variable, even if type checking is disabled. """
REQUIRED_STRING = "__required__string"
REQUIRED_INT = "__required__int"
REQUIRED_FLOAT = "__required__float"
REQUIRED_LIST = "__required__list"
REQUIRED_DICT = "__required__dict"
REQUIRED_DATETIME = "__required__datetime"
REQUIRED_OBJECTID = "__required__object_id"

REQUIRED_VALUES = [REQUIRED, REQUIRED_STRING, REQUIRED_INT, REQUIRED_FLOAT,
                   REQUIRED_LIST, REQUIRED_DICT, REQUIRED_DATETIME, REQUIRED_OBJECTID]

REQUIRED_TYPES = {
    REQUIRED_STRING: basestring,
    REQUIRED_INT: int,
    REQUIRED_FLOAT: float,
    REQUIRED_LIST: list,
    REQUIRED_DICT: dict,
    REQUIRED_DATETIME: datetime,
    REQUIRED_OBJECTID: ObjectId
}

""" Indicates that a key in DatabaseObject.DEFAULTS is to be used in update
    operations; treated as REQUIRED in current library version """
UPDATE = "__update__"

""" PATH definition to be used by DatabaseObject children classes that are
    not meant to be used as database accessors themselves, but rather extract
    common functionality used by DatabaseObjects of various collections"""
CHILD_TEMPLATE = "CHILD_TEMPLATE"

""" Name of the database used in test mode """
TEST_DATABASE_NAME = "__MONGOLIA_TEST_DATABASE__"
