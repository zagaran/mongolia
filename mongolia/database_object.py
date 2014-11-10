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

from logging import log, WARN

from mongolia.constants import ID_KEY, CHILD_TEMPLATE, REQUIRED, UPDATE
from mongolia.errors import (TemplateDatabaseError, MalformedObjectError,
    RequiredKeyError, DatabaseConflictError, InvalidKeyError)
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
    as item accessers.  This means that you can access elements in the
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
    
    def __init__(self, query=None, path=None, defaults=None, _new_object=False, **kwargs):
        """
        Loads a single database object from path matching query.  If nothing
        matches the query (possibly because there is nothing in the specified
        mongo collection), the created DatabaseObject will be an empty
        dictionary and have bool(returned object) == False.
        
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
        """
        if path:
            dict.__setattr__(self, "PATH", path)
        if defaults:
            dict.__setattr__(self, "DEFAULTS", defaults)
        if self.PATH == CHILD_TEMPLATE:
            raise TemplateDatabaseError()
        dict.__setattr__(self, "_collection", self.db(self.PATH))
        if _new_object:
            dict.__init__(self, _new_object)
            return
        if query is None and len(kwargs) > 0:
            query=kwargs
        if query is not None:
            data = self.db(path).find_one(query)
            if data is not None:
                dict.__init__(self, data)
    
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
            query=kwargs
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
            "database.colletion"
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
        if random_id and ID_KEY in self:
            dict.__delitem__(self, ID_KEY)
        if not random_id and ID_KEY not in self:
            raise MalformedObjectError("No " + ID_KEY + " key in item") 
        if not random_id and not overwrite and self._collection.find_one({ID_KEY: data[ID_KEY]}):
            raise DatabaseConflictError('ID_KEY "%s" already exists in collection %s' %
                                        (data[ID_KEY], self.PATH))
        self.save()
        return self
    
    @classmethod
    def db(cls, path=None):
        """
        Returns a pymongo Collection object from the current database connection 
        
        @param path: if is None, the PATH attribute of the current class is used;
            if is not None, this is used instead
            
        @raise Exception: if neither cls.PATH or path are valid
        """
        if cls.PATH is None and path is None:
            raise Exception("No database specified")
        if path is not None:
            if "." not in path:
                raise Exception(('invalid path "%s"; database paths must be ' +
                                 'of the form "database.collection"') % (path,))
            (db, coll) = path.split('.', 1)
        else:
            if "." not in cls.PATH:
                raise Exception(('invalid path "%s"; database paths must be ' +
                                 'of the form "database.collection"') % (cls.PATH,))
            (db, coll) = cls.PATH.split('.', 1)
        return CONNECTION.get_connection()[db][coll] 
    
    @classmethod
    def _get_from_defaults(cls, key):
        if cls.DEFAULTS[key] == REQUIRED:
            raise RequiredKeyError(key)
        if cls.DEFAULTS[key] == UPDATE:
            raise KeyError(key)
        try:
            # Try DEFAULTS as a function
            default = cls.DEFAULTS[key]()
        except TypeError:
            # If it fails, treat DEFAULTS entry as a value
            default = cls.DEFAULTS[key]
        # If default is a dict or a list, make a copy to avioid passing by reference
        if isinstance(default, list):
            default = list(default)
        if isinstance(default, dict):
            default = dict(default)
        return default
    
    def __getitem__(self, name):
        if name == "ID_KEY":
            return self[ID_KEY]
        if name in self:
            return dict.__getitem__(self, name)
        try:
            new = self._get_from_defaults(name)
        except RequiredKeyError:
            raise MalformedObjectError('"%s" is a required key of %s' %
                                       (name, type(self).__name__))
        dict.__setitem__(self, name, new)
        return new
    
    def __setitem__(self, key, value):
        if key == ID_KEY or key == "ID_KEY":
            raise KeyError("Do not modify '%s' directly; use rename() instead" % ID_KEY)
        if self.DEFAULTS and key not in self.DEFAULTS:
            if CONNECTION.defaults_handling == AlertLevel.error:
                raise InvalidKeyError("%s not in DEFAULTS for %s" % (key, type(self).__name__))
            elif CONNECTION.default_handling == AlertLevel.warning:
                log(WARN, "%s not in DEFAULTS for %s" % (key, type(self).__name__))
        dict.__setitem__(self, key, value)
    
    def __delitem__(self, name):
        if name in self:
            dict.__delitem__(self, name)
    
    def __getattr__(self, name):
        return self[name]
    
    def __setattr__(self, name, val):
        self[name] = val
        
    def __delattr__(self, name):
        del self[name]
    
    def __dir__(self):
        return sorted(set(dir(type(self)) + self.keys()))
    
    def save(self):
        """
        Saves the current state of the DatabaseObject to the database.  Fills
        in missing values from defaults before saving.
        
        NOTE: The actual operation here is to overwrite the entry in the
        database with the same ID_KEY.
        
        WARNING: While the save operation itself is atomic, it is not atomic
        with loads and modifications to the object.  You must provide your own
        synchronization if you have multiple threads or processes possibly
        modifying the same database object.
        
        @raise MalformedObjectError: if the object does not provide a value
            for a REQUIRED default
        """
        # Fill in missing defaults by invoking __getitem__ for each key in DEFAULTS 
        for key in self.DEFAULTS:
            try: self[key]
            except KeyError: pass
        new_id = self._collection.save(dict(self))
        dict.__setitem__(self, ID_KEY, new_id)
    
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
    
    def copy(self, new_id):
        """
        Copies the DatabaseObject under the ID_KEY new_id.
        
        @param new_id: the value for ID_KEY of the copy
        """
        data = dict(self)
        data[ID_KEY] = new_id
        self.create(data)
