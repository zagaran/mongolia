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

""" Special key required by mongo for all DatabaseObjects; uniquely
    identifies DatabaseObjects """
ID_KEY = "_id"

""" Not used in current library version """
INC = "$inc"

""" Greater than argument to mongo query """
GT = "$gt"

""" Indicates that a key in DatabaseObject.DEFAULTS is required """
REQUIRED = "__required__"

""" Indicates that a key in DatabaseObject.DEFAULTS is to be used in update
    operations; treated as REQUIRED in current library version """
UPDATE = "__update__"

""" PATH definition to be used by DatabaseObject children classes that are
    not meant to be used as database accessors themselves, but rather extract
    common functionality used by DatabaseObjects of various collections"""
CHILD_TEMPLATE = "CHILD_TEMPLATE"
