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

import collections
import json

from logging import log, WARN
from mongolia.constants import (ID_KEY, CHILD_TEMPLATE, UPDATE, SET,
    REQUIRED_VALUES, REQUIRED_TYPES, TYPES_TO_CHECK, TEST_DATABASE_NAME)
from mongolia.errors import (TemplateDatabaseError, MalformedObjectError,
    RequiredKeyError, DatabaseConflictError, InvalidKeyError, InvalidTypeError,
    NonexistentObjectError)
from mongolia.json_codecs import MongoliaJSONEncoder, MongoliaJSONDecoder
from mongolia.mongo_connection import CONNECTION, AlertLevel

class DatabaseObject(dict):
    """
    Represent a MongoDB object as a Python dictionary.
        
    PATH is the database path in the form "database.collection"; children
        classes of DatabaseObject should override this attribute.
        PATH is what specifies which collection in mongo an item is stored in.
        PATH SHOULD BE UNIQUE FOR EACH CHILD OF DatabaseObject.
        IF TWO DatabaseObjects ARE CREATED WITH THE SAME PATH, THEIR DATA
        WILL BE STORED IN THE SAME COLLECTION.
    
    DEFAULTS is a dictionary of default values for keys of the dict;
        defaults can be functions; REQUIRED is a special value for a key that
        raises a MalformedObjectError if that key isn't in the dict at save
        time; ; children classes of DatabaseObject can optionally override
        this attribute
    
    
    Child Class Example:
    
    class User(DatabaseObject):
        PATH = "application.users"
        DEFAULTS = {
            "email": REQUIRED,
            "password": REQUIRED,
            "time_created": datetime.now,
            "name": "anonymous"
        }
        
    __getattr__, __setattr__, and __delattr__ have been overridden to behave
    as item accessors.  This means that you can access elements in the
    DatabaseObject by either database_object["key"] or database_object.key;
    database_object["key"] syntax is preferable for use in production code
    since there is no chance of conflicting with any of the methods attached
    to the DatabaseObject.  For example, if your entry is named "copy", you can
    only access it by means of database_object["copy"], as database_object.copy
    gives lookup preference to the .copy() method.  Mostly, the ability to
    use the attribute access is for convenience when interacting with
    DatabaseObjects in an interactive python shell.
    
    """
    PATH = None
    DEFAULTS = {}
    _exists = True
    
    def __init__(self, query=None, path=None, defaults=None, _new_object=None, **kwargs):
        """
        Loads a single database object from path matching query.  If nothing
        matches the query (possibly because there is nothing in the specified
        mongo collection), the created DatabaseObject will be an empty
        dictionary and have bool(returned object) == False.  If more than one
        database object matches the query, a DatabaseConflictError is thrown.
        
        NOTE: The path and defaults parameters to this function are to allow
        use of the DatabaseObject class directly.  However, this class is
        intended for subclassing and children of it should override the PATH
        and DEFAULTS attributes rather than passing them as parameters here.
        
        NOTE: if you pass in a single argument to __init__, this will
        match against ID_KEY.
        
        @param query: a dictionary specifying key-value pairs that the result
            must match.  If query is None, use kwargs in it's place
        @param path: the path of the database to query, in the form
            "database.colletion"; pass None to use the value of the
            PATH property of the object
        @param defaults: the defaults dictionary to use for this object;
            pass None to use the DEFAULTS property of the object
        @param _new_object: internal use only
        @param **kwargs: used as query parameters if query is None
        
        @raise Exception: if path and self.PATH are None; the database path
            must be defined in at least one of these
        @raise TemplateDatabaseError: if PATH is CHILD_TEMPLATE; this
            constant is for children classes that are not meant to be
            used as database accessors themselves, but rather extract
            common functionality used by DatabaseObjects of various collections
        @raise DatabaseConflictError: if PATH is CHILD_TEMPLATE; this
            constant is for children classes that are not meant to be
            used as database accessors themselves, but rather extract
            common functionality used by DatabaseObjects of various collections
        """
        if path:
            dict.__setattr__(self, "PATH", path)
        if defaults:
            dict.__setattr__(self, "DEFAULTS", defaults)
        if self.PATH == CHILD_TEMPLATE:
            raise TemplateDatabaseError()
        dict.__setattr__(self, "_collection", self.db(self.PATH))
        if _new_object is not None:
            dict.__init__(self, _new_object)
            return
        if query is None and len(kwargs) > 0:
            query = kwargs
        if query is not None:
            if not isinstance(query, collections.Mapping):
                query = {ID_KEY: query}
            cursor = self.db(path).find(query)
            if cursor.count() > 1:
                raise DatabaseConflictError(('More than one database object ' +
                                             'was found for query "%s"') % (query, ))
            for result in cursor.limit(-1):
                dict.__init__(self, result)
                return
        dict.__setattr__(self, "_exists", False)
    
    @classmethod
    def exists(cls, query=None, path=None, **kwargs):
        """
        Like __init__ but simply returns a boolean as to whether or not the
        object exists, rather than returning the whole object.
        
        NOTE: if you pass in a single argument to exists, this will
        match against ID_KEY.
        
        @param query: a dictionary specifying key-value pairs that the result
            must match.  If query is None, use kwargs in it's place
        @param path: the path of the database to query, in the form
            "database.colletion"; pass None to use the value of the
            PATH property of the object
        @param **kwargs: used as query parameters if query is None
        
        @raise Exception: if path and self.PATH are None; the database path
            must be defined in at least one of these
        """
        if query is None and len(kwargs) > 0:
            query = kwargs
        if query is None:
            return False
        return cls.db(path).find_one(query) is not None
    
    @classmethod
    def create(cls, data, path=None, defaults=None, overwrite=False,
               random_id=False, **kwargs):
        """
        Creates a new database object and stores it in the database
        
        NOTE: The path and defaults parameters to this function are to allow
        use of the DatabaseObject class directly.  However, this class is
        intended for subclassing and children of it should override the PATH
        and DEFAULTS attributes rather than passing them as parameters here.
        
        @param data: dictionary of data that the object should be created with;
            this must follow all mongo rules, as well as have an entry for
            ID_KEY unless random_id == True
        @param path: the path of the database to use, in the form
            "database.collection"
        @param defaults: the defaults dictionary to use for this object
        @param overwrite: if set to true, will overwrite any object in the
            database with the same ID_KEY; if set to false will raise an
            exception if there is another object with the same ID_KEY
        @param random_id: stores the new object with a random value for ID_KEY;
            overwrites data[ID_KEY]
        @param **kwargs: ignored
        
        @raise Exception: if path and self.PATH are None; the database path
            must be defined in at least one of these
        @raise DatabaseConflictError: if there is already an object with that
            ID_KEY and overwrite == False
        @raise MalformedObjectError: if a REQUIRED key of defaults is missing,
            or if the ID_KEY of the object is None and random_id is False
        """
        self = cls(path=path, defaults=defaults, _new_object=data)
        for key, value in self.items():
            if key == ID_KEY:
                continue
            if self.DEFAULTS and key not in self.DEFAULTS:
                self._handle_non_default_key(key, value)
            self._check_type(key, value)
        if random_id and ID_KEY in self:
            dict.__delitem__(self, ID_KEY)
        if not random_id and ID_KEY not in self:
            raise MalformedObjectError("No " + ID_KEY + " key in item")
        if not random_id and not overwrite and self._collection.find_one({ID_KEY: data[ID_KEY]}):
            raise DatabaseConflictError('ID_KEY "%s" already exists in collection %s' %
                                        (data[ID_KEY], self.PATH))
        self._pre_save()
        if ID_KEY in self and overwrite:
            self._collection.replace_one({ID_KEY: self[ID_KEY]}, dict(self), upsert=True)
        else:
            insert_result = self._collection.insert_one(dict(self))
            dict.__setitem__(self, ID_KEY, insert_result.inserted_id)
        return self
    
    @classmethod
    def create_from_json(cls, json_str, ignore_non_defaults=True):
        """
        Creates a database object from a json object.  The intent of this method
        is to allow creating a database object directly from json.
        
        Mongolia will also automatically convert any json values that are
        formatted using the MongoliaJSONEncoder (for ObjectIds and datetime
        objects) back to their native python data types.
        
        Note: if using AngularJS, make sure to pass json back using
        `angular.toJson(obj)` instead of `JSON.stringify(obj)` since angular
        sometimes adds `$$hashkey` to javascript objects and this will cause
        a mongo error due to the "$" prefix in keys.
        
        @param json_str: the json string containing the new object to use for
            creating the new object
        @param ignore_non_defaults: if this is True and the database object
            has non-empty DEFAULTS, then any top-level keys of the create json
            that do not appear in DEFAULTS will also be excluded in creation
        """
        create_dict = json.loads(json_str, cls=MongoliaJSONDecoder, encoding="utf-8")
        # Remove all keys not in DEFAULTS if ignore_non_defaults is True
        if cls.DEFAULTS and ignore_non_defaults:
            for key in frozenset(create_dict).difference(frozenset(cls.DEFAULTS)):
                del create_dict[key]
        
        cls.create(create_dict, random_id=True)
    
    @classmethod
    def db(cls, path=None):
        """
        Returns a pymongo Collection object from the current database connection.
        If the database connection is in test mode, collection will be in the
        test database.
        
        @param path: if is None, the PATH attribute of the current class is used;
            if is not None, this is used instead
        
        @raise Exception: if neither cls.PATH or path are valid
        """
        if cls.PATH is None and path is None:
            raise Exception("No database specified")
        if path is None:
            path = cls.PATH
        if "." not in path:
            raise Exception(('invalid path "%s"; database paths must be ' +
                             'of the form "database.collection"') % (path,))
        if CONNECTION.test_mode:
            return CONNECTION.get_connection()[TEST_DATABASE_NAME][path]
        (db, coll) = path.split('.', 1)
        return CONNECTION.get_connection()[db][coll]
    
    def __getitem__(self, key):
        if not self._exists:
            raise NonexistentObjectError("The object does not exist")
        if key == ID_KEY or key == "ID_KEY":
            return dict.__getitem__(self, ID_KEY)
        elif key in self:
            value = dict.__getitem__(self, key)
            self._check_type(key, value, warning_only=True)
            return value
        try:
            new = self._get_from_defaults(key)
        except RequiredKeyError:
            raise MalformedObjectError("'%s' is a required key of %s" %
                                       (key, type(self).__name__))
        dict.__setitem__(self, key, new)
        return new
    
    def __setitem__(self, key, value):
        if not self._exists:
            raise NonexistentObjectError("The object does not exist")
        if key == ID_KEY or key == "ID_KEY":
            # Do not allow setting ID_KEY directly
            raise KeyError("Do not modify '%s' directly; use rename() instead" % ID_KEY)
        if not isinstance(key, basestring):
            raise InvalidKeyError("documents must have only string keys, key was %s" % key)
        if self.DEFAULTS and key not in self.DEFAULTS:
            self._handle_non_default_key(key, value)
        self._check_type(key, value)
        dict.__setitem__(self, key, value)
    
    def __delitem__(self, key):
        if not self._exists:
            raise NonexistentObjectError("The object does not exist")
        if key == ID_KEY or key == "ID_KEY":
            # Do not allow deleting ID_KEY
            raise KeyError("Do not delete '%s' directly; use rename() instead" % ID_KEY)
        if key in self:
            dict.__delitem__(self, key)
    
    def __getattr__(self, key):
        return self[key]
    
    def __setattr__(self, key, val):
        self[key] = val
        
    def __delattr__(self, key):
        del self[key]
    
    def __dir__(self):
        return sorted(set(dir(type(self)) + self.keys()))
    
    def _pre_save(self):
        if not self._exists:
            raise NonexistentObjectError("The object does not exist")
        # Fill in missing defaults by invoking __getitem__ for each key in DEFAULTS
        for key in self.DEFAULTS:
            try:
                self[key]
            except KeyError:
                pass
    
    def save(self):
        """
        Saves the current state of the DatabaseObject to the database.  Fills
        in missing values from defaults before saving.
        
        NOTE: The actual operation here is to overwrite the entry in the
        database with the same ID_KEY.
        
        WARNING: While the save operation itself is atomic, it is not atomic
        with loads and modifications to the object.  You must provide your own
        synchronization if you have multiple threads or processes possibly
        modifying the same database object.  The update method is better from
        a concurrency perspective.
        
        @raise MalformedObjectError: if the object does not provide a value
            for a REQUIRED default
        """
        self._pre_save()
        self._collection.replace_one({ID_KEY: self[ID_KEY]}, dict(self))
    
    def rename(self, new_id):
        """
        Renames the DatabaseObject to have ID_KEY new_id.  This is the only
        way allowed by DatabaseObject to change the ID_KEY of an object.
        Trying to modify ID_KEY in the dictionary will raise an exception.
        
        @param new_id: the new value for ID_KEY
        
        NOTE: This is actually a create and delete.
        
        WARNING: If the system fails during a rename, data may be duplicated.
        """
        old_id = dict.__getitem__(self, ID_KEY)
        dict.__setitem__(self, ID_KEY, new_id)
        self._collection.save(self)
        self._collection.remove({ID_KEY: old_id})
    
    def remove(self):
        """
        Deletes the object from the database
        
        WARNING: This cannot be undone.  Be really careful when deleting
        programatically.  It is recommended to backup your database before
        applying specific deletes.  If your application uses deletes regularly,
        it is strongly recommended that you have a recurring backup system.
        """
        self._collection.remove({ID_KEY: self[ID_KEY]})
        dict.clear(self)
    
    def copy(self, new_id=None, attribute_overrides={}):
        """
        Copies the DatabaseObject under the ID_KEY new_id.
        
        @param new_id: the value for ID_KEY of the copy; if this is none,
            creates the new object with a random ID_KEY
        @param attribute_overrides: dictionary of attribute names -> values that you would like to override with.
        """
        data = dict(self)
        data.update(attribute_overrides)
        if new_id is not None:
            data[ID_KEY] = new_id
            return self.create(data, path=self.PATH)
        else:
            del data[ID_KEY]
            return self.create(data, random_id=True, path=self.PATH)

    def update(self, update_dict=None, **kwargs):
        """
        Applies updates both to the database object and to the database via the
        mongo update method with the $set argument.
        
        WARNING: While the update operation itself is atomic, it is not atomic
        with loads and modifications to the object.  You must provide your own
        synchronization if you have multiple threads or processes possibly
        modifying the same database object.  While this is safer from a
        concurrency perspective than the access pattern load -> modify -> save
        as it only updates keys specified in the update_dict, it will still
        overwrite updates to those same keys that were made while the object
        was held in memory.
        
        @param update_dict: dictionary of updates to apply
        @param **kwargs: used as update_dict if no update_dict is None
        """
        if update_dict is None:
            update_dict = kwargs
        for key, value in update_dict.items():
            self._check_type(key, value)
        dict.update(self, update_dict)
        self.db(self.PATH).update_one({ID_KEY: self[ID_KEY]}, {SET: update_dict})
    
    def to_json(self):
        """
        Returns the json string of the database object in utf-8.
        
        Note: ObjectId and datetime.datetime objects are custom-serialized
        using the MongoliaJSONEncoder because they are not natively json-
        serializable.
        """
        return json.dumps(self, cls=MongoliaJSONEncoder, encoding="utf-8")
    
    def json_update(self, json_str, exclude=[], ignore_non_defaults=True):
        """
        Updates a database object based on a json object.  The intent of this
        method is to allow passing json to an interface which then subsequently
        manipulates the object and then sends back an update.
        
        Mongolia will also automatically convert any json values that were
        initially converted from ObjectId and datetime.datetime objects back
        to their native python object types.
        
        Note: if using AngularJS, make sure to pass json back using
        `angular.toJson(obj)` instead of `JSON.stringify(obj)` since angular
        sometimes adds `$$hashkey` to javascript objects and this will cause
        a mongo error due to the "$" prefix in keys.
        
        @param json_str: the json string containing the new object to use for
            the update
        @param exclude: a list of top-level keys to exclude from the update
            (ID_KEY need not be included in this list; it is automatically
            deleted since it can't be part of a mongo update operation)
        @param ignore_non_defaults: if this is True and the database object
            has non-empty DEFAULTS, then any top-level keys in the update json
            that do not appear in DEFAULTS will also be excluded from the update
        """
        update_dict = json.loads(json_str, cls=MongoliaJSONDecoder, encoding="utf-8")
        # Remove ID_KEY since it can't be part of a mongo update operation
        if ID_KEY in update_dict:
            del update_dict[ID_KEY]
        
        # Remove all keys in the exclude list from the update
        for key in frozenset(exclude).intersection(frozenset(update_dict)):
            del update_dict[key]
        
        # Remove all keys not in DEFAULTS if ignore_non_defaults is True
        if self.DEFAULTS and ignore_non_defaults:
            for key in frozenset(update_dict).difference(frozenset(self.DEFAULTS)):
                del update_dict[key]
        
        self.update(update_dict)
    
    def json_update_fields(self, json_str, fields_to_update):
        """
        Updates the specified fields of a database object based on a json
        object. The intent of this method is to allow passing json to an
        interface which then subsequently manipulates the object and then sends
        back an update for specific fields of the object.
        
        Mongolia will also automatically convert any json values that were
        initially converted from ObjectId and datetime.datetime objects back
        to their native python object types.
        
        Note: if using AngularJS, make sure to pass json back using
        `angular.toJson(obj)` instead of `JSON.stringify(obj)` since angular
        sometimes adds `$$hashkey` to javascript objects and this will cause
        a mongo error due to the "$" prefix in keys.
        
        @param json_str: the json string containing the new object to use for
            the update
        @param fields_to_update: a list of the top-level keys to update; only
            keys included in this list will be update.  Do not include ID_KEY
            in this list since it can't be part of a mongo update operation
        """
        update_dict = json.loads(json_str, cls=MongoliaJSONDecoder, encoding="utf-8")
        update_dict = dict((k, v) for k, v in update_dict.items()
                       if k in fields_to_update and k != ID_KEY)
        self.update(update_dict)
    
    def _get_from_defaults(self, key):
        # If a KeyError is raised here, it is because the key is found in
        # neither the database object nor the DEFAULTS
        if self.DEFAULTS[key] in REQUIRED_VALUES:
            raise RequiredKeyError(key)
        if self.DEFAULTS[key] == UPDATE:
            raise KeyError(key)
        try:
            # Try DEFAULTS as a function
            default = self.DEFAULTS[key]()
        except TypeError:
            # If it fails, treat DEFAULTS entry as a value
            default = self.DEFAULTS[key]
        # If default is a dict or a list, make a copy to avoid passing by reference
        if isinstance(default, list):
            default = list(default)
        if isinstance(default, dict):
            default = dict(default)
        return default
    
    def _handle_non_default_key(self, key, value):
        # There is an attempt to set a key not in DEFAULTS
        if CONNECTION.defaults_handling == AlertLevel.error:
            raise InvalidKeyError("%s not in DEFAULTS for %s" %
                                  (key, type(self).__name__))
        elif CONNECTION.defaults_handling == AlertLevel.warning:
            log(WARN, "%s not in DEFAULTS for %s" % (key, type(self).__name__))
    
    def _check_type(self, key, value, warning_only=False):
        # Check the type of the object against the type in DEFAULTS
        if not self.DEFAULTS or key not in self.DEFAULTS:
            # If the key is not in defaults, there is nothing to compare to
            return
        default = self.DEFAULTS[key]
        if default in REQUIRED_TYPES.keys() and not isinstance(value, REQUIRED_TYPES[default]):
            # Check types of required fields regardless of alert settings
            message = ("value '%s' for key '%s' must be of type %s" %
                       (value, key, REQUIRED_TYPES[default]))
            if warning_only:
                log(WARN, message)
                return
            raise InvalidTypeError(message)
        if default in REQUIRED_VALUES or default == UPDATE:
            # Handle special keys, including a REQUIRED_TYPE default
            # (which was checked above)
            return
        
        if CONNECTION.type_checking == AlertLevel.none:
            # Shortcut return if type checking is disabled
            return
        type_ = DatabaseObject._get_type(default)
        if type_ is None or isinstance(value, type_):
            # The key either matches the type of the default or the default is
            # not one of the types we check; everything is good
            return
        # If we've gotten here, there is a type mismatch: warn or error
        message = ("value '%s' for key '%s' must be of type %s" %
                   (value, key, type_))
        if CONNECTION.type_checking == AlertLevel.error:
            if warning_only:
                log(WARN, message)
                return
            raise InvalidTypeError(message)
        elif CONNECTION.type_checking == AlertLevel.warning:
            log(WARN, message)
    
    @staticmethod
    def _get_type(default):
        for type_ in TYPES_TO_CHECK:
            if isinstance(default, type_):
                return type_
        return None


