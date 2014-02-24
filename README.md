Mongolia
========

Mongolia is a wrapper of the pymongo library that lets you work with your mongo objects in a much more pythonic way.

+++ DatabaseObject

By extending the python dictionary class, a DatabaseObject lets you interact with the database directly through the items stored in it.  These are simply dictionaries with a few extra methods:

[[code type="Python"]]
from mongolia import DatabaseObject, ID_KEY
path = "somedb.somecoll"

# Put a new item in the database
item = DatabaseObject.create({ID_KEY: "stuff", "key": "value"}, db=path)

# Modify the item and re-save it
item["key"] = "newval"
item.save()

# Get an item out of the database
item = DatabaseObject("stuff", db=path)
    # or just
item = DatabaseObject("stuff", path)

# Load an item by attribute rather than _id
item = DatabaseObject({"key": "newval"}, db=path)
    # or just
item = DatabaseObject(db=path, key="newval")

# Delete an item by
item.remove()

# Rename an item (changing it's ID_KEY)
item.rename("different_stuff")

[[/code]]

It is worth noting that the ID_KEY of a dictionary (defined by Mongo as "_id") is always a required key of the DatabaseObject (so it will be an error if you try to create a DatabaseObject without either giving it an ID_KEY entry or setting random_id=True).  When updating a DatabaseObject, changing the ID_KEY is also an error (as this is used by mongo to enforce uniqueness); instead, use the "rename" method.

+++ DatabaseCollection

DatabaseCollection returns a collection as an explicit list of DatabaseObjects.  When using this on larger collections, you can run out of memory, so use filtering or pagination.  Usage looks like this:

[[code type="Python"]]
from mongolia import DatabaseCollection
path = "somedb.somecoll"

# Returns the entire collection
coll = DatabaseCollection(path)

# Returns the first ten elements of the collection (pages are 1-indexed for UI reasons)
coll = DatabaseCollection(path, page=1, page_size=10)

# Returns the number of elements in the collection
count = DatabaseCollection.count(path)

# Returns a specific filtering of the collection
coll = DatabaseCollection(path, query={"key": "newval"})
  # or just
coll = DatabaseCollection(path, key="newval")

# Returns a read-only copy of the collection
# (the items in the list will just be dicts, not DatabaseObjects, so you can't save them)
coll = DatabaseCollection(path, readonly=True)

# Returns a list of a specific field of elements in the collection
# (the following returns a list of _id's in the collection)
coll = DatabaseCollection(path, field="_id")
[[/code]]

+++ Subclasses and ORM

By subclassing DatabaseObject and DatabaseCollection, you can use mongolia as a full-fledged ORM (Object Relatiional Mapping; techinally this may be an OODBMS, but who cares).

Subclasses of DatabaseObject and DatabaseCollection, db arguments have already been specified and need not be included.  Thus, one could make a User subclass and do the following with it:
[[code type="python"]]
class User(DatabaseObject):
    PATH = "somedb.users"

class Users(DatabaseCollection):
    OBJTYPE = User

# load a user
user = User("user_id")

# load all users
users = Users()

# load all users with a particular setting
users = Users(status="active")

[[/code]]

Also possibly present in a subclass is a DEFAULTS dictionary.  This is a list of keys that can be assumed to be in the dictionary because when a DatabaseObject is saved or a value is pulled from it, any entry is completed from the DEFAULTS dictionary for that object.  REQUIRED is a special key that indicates that the key in question is required for the object but there is no default.  If a subclass of DatabaseObject is saved without an entry for a REQUIRED key, an error will be thrown.  Note that ID_KEY is implicitly a REQUIRED key of all DatabaseObjects.

Values in the DEFAULTS dictionary may be either constants or functions; the differentiation is handled automatically by DatabaseObject.  Best practice when modifying a function in the DEFAULTS dictionary is to go through the collection it is used on and re-save every item (thus applying the new function).  Examples follow:

[[code type="python"]]
from mongolia import DatabaseObject, ID_KEY, REQUIRED, DatabaseCollection
from datetime import datetime

class TestObject(DatabaseObject):
    PATH = "test.test"
    DEFAULTS = {"description": REQUIRED, "metadata": None, "created": datetime.now}

# New objects must have required keys:
TestObject.create({ID_KEY: "test1"})
# raises mongolia.database_dict.MalformedObjectError:
#     "description" is a required key of TestObject

# When an object is saved, DEFAULTS are applied:
TestObject.create({ID_KEY: "test1", "description": "this is a test"})
# returns {'metadata': None, '_id': 'test1', 'description': 'this is a test',
#          'created': datetime.datetime(2012, 12, 11, 14, 14, 13, 754589)}


# Here is a decent way to handle a new function in DEFAULTS (if we didn't do this,
# then test_object["metadata"] would almost certainly have different values
# between loads of the object):
from random import random
class TestObject(DatabaseObject):
    PATH = "test.test"
    DEFAULTS = {"description": REQUIRED, "metadata": random,
                    "created": datetime.now}

class TestObjects(DatabaseCollection):  OBJTYPE = TestObject

# This is the line we have to run to update every object in the collection:
for test_object in TestObjects(): test_object.save()
[[/code]]

+++ Dealing with Large Collections

Mongolia gets good perfomance by loading entire collections into memory at query time.  This is fine until your collections get large.  In this case, to avoid running out of memory, you will want to use mongolia's memory-effient colleciton iterator.  It fetches items in pages to limit memory use, but pages efficiently to keep the iteration linear instead of quadratic in runtime (a problem with pymongo's built-in paging).

[[code type="python"]]
# iterate over users
for user in Users.iterator():
    do_some_code(user)

# iterate over a subset of users
for user in Users.iterator(status="active"):
    do_some_code(user)
[[/code]]

