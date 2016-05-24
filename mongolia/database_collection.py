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

import json
from pymongo import ASCENDING, DESCENDING

from mongolia.constants import ID_KEY, GT
from mongolia.database_object import DatabaseObject
from mongolia.json_codecs import MongoliaJSONEncoder


class DatabaseCollection(list):
    """
    Represent a MongoDB collection as a Python list of DatabaseObjects.
    
    OBJTYPE is a child class of DatabaseObject; this is the type of object
        to be used in the retrieval of database objects; children
        classes of DatabaseCollection should override this attribute
    
    PATH is the database path in the form "database.collection";
        if not None, this overrides the PATH attribute of OBJTYPE;
        if is None, then the PATH attribute of OBJTYPE is used instead;
        children classes of DatabaseCollection can optionally override this
        attribute, but defining PATH through OBJTYPE is preferable
    
    
    Child Class Example:
    
    class User(DatabaseObject):
        PATH = "application.users"
        DEFAULTS = {
            "email": REQUIRED,
            "password": REQUIRED,
            "time_created": datetime.now,
            "name": "anonymous"
        }
        
    class Users(DatabaseCollection):
        OBJTYPE = User
    """
    OBJTYPE = DatabaseObject
    PATH = None
    
    def __init__(self, path=None, objtype=None, query=None, sort_by=ID_KEY, ascending=True,
                 page=0, page_size=None, read_only=False, projection=None, field=None,
                 **kwargs):
        """
        Loads a list of DatabaseObjects from path matching query.  If nothing
        matches the query (possibly because there is nothing in the specified
        mongo collection), the created DatabaseCollection will be an empty
        list and have bool(returned object) == False
        
        NOTE: The path and objtype parameters to this function are to allow
        use of the DatabaseCollection class directly.  However, this class is
        intended for subclassing and children of it should override either the
        OBJTYPE or PATH attribute rather than passing them as parameters here.
        
        WARNING: if you are attempting to grab a particularly large set of
        results (such as an entire collection), your system may run out of
        memory.  In the event of large collections, the number of returned
        results can be reduced either by filtering the results with the query
        parameter or by using pagination via the page_size and page parameters.
        If all you need to do is iterate over the collection, use the `iterator`
        classmethod.
        
        @param path: the path of the database to query, in the form
            "database.colletion"; pass None to use the value of the
            PATH property of the object or, if that is none, the
            PATH property of OBJTYPE
        @param objtype: the object type to use for these DatabaseObjects;
            pass None to use the OBJTYPE property of the class
        @param query: a dictionary specifying key-value pairs that the result
            must match.  If query is None, use kwargs in it's place
        @param sort_by: a key to use for the sort order of the results; ID_KEY
            by default. Can also be a list of pairs [(key, direction), ...], as
            in pymongo's sort function. If set to None, no sort operation is
            applied.
        @param ascending: whether to sort the results in ascending order of
            the sort_by key (if True) or descending order (if False). Ignored if
            sort_by is a list or None.
        @param page: the page number of results to return if pagination is
            being uses; note that if page_size is None, this parameter is
            ignored; page is 0-indexed
        @param page_size: returns only a single page of results, this
            defining the number of results in a page; see also the page
            parameter; if this is None or 0, paging is disabled
        @param read_only: returns the contents as python dictionaries rather than
            DatabaseObjects.  This is not read_only in the sense that the
            returned objects are immutable, but in the sense that they have no
            attached .save() methods, so there is no way to write modifications
            to them back to the database.
        @param projection: specifies fields to return in a projection query. May
            be a list of field names, in which case the ID_KEY field is always
            returned whether or not listed. To prevent ID_KEY from being
            included, use a dict instead (see pymongo documentation for
            projection queries). Specifying this field implies read_only.
        @param field: returns simply the indicated field for each object
            rather than the entire object.  For example, if ID_KEY is passed in
            for this parameter, only the ID's of the collection are returned,
            not the entire contents.  This behaves similarly to read_only
            in that the returned objects cannot be saved to the database if
            they are updated.  Objects that do not have the indicated field
            are omitted from results. Do not combine with the projection parameter.
        @param **kwargs: used as query parameters if query is None
        
        @raise Exception: if path, self.PATH, and self.OBJTYPE.PATH are all
            None; the database path must be defined in at least one of these
        """
        if objtype:
            self.OBJTYPE = objtype
        if path:
            self.PATH = path
        if not query:
            query = kwargs
        if field:
            if field == ID_KEY:
                projection = [ID_KEY]
            else:
                projection = {field: True, ID_KEY: False}
        if projection:
            read_only = True
        results = self.db().find(query, projection=projection)    
        if isinstance(sort_by, list):
            results = results.sort(sort_by)
        elif sort_by:
            results = results.sort(sort_by, ASCENDING if ascending else DESCENDING)
        if page_size:
            results.limit(page_size).skip(page_size * page)
        if field:
            for result in results:
                if field in result:
                    self.append(result[field])
        elif read_only:
            for result in results:
                self.append(result)
        else:
            for result in results:
                self.append(self.OBJTYPE(path=self.PATH, _new_object=result))
    
    @classmethod
    def count(cls, path=None, objtype=None, query=None, **kwargs):
        """
        Like __init__, but simply returns the number of objects that match the
        query rather than returning the objects
        
        NOTE: The path and objtype parameters to this function are to allow
        use of the DatabaseCollection class directly.  However, this class is
        intended for subclassing and children of it should override either the
        OBJTYPE or PATH attribute rather than passing them as parameters here.
        
        @param path: the path of the database to query, in the form
            "database.colletion"; pass None to use the value of the
            PATH property of the object or, if that is none, the
            PATH property of OBJTYPE
        @param objtype: the object type to use for these DatabaseObjects;
            pass None to use the OBJTYPE property of the class
        @param query: a dictionary specifying key-value pairs that the result
            must match.  If query is None, use kwargs in it's place
        @param **kwargs: used as query parameters if query is None
        
        @raise Exception: if path, PATH, and OBJTYPE.PATH are all None;
            the database path must be defined in at least one of these
        """
        if not objtype:
            objtype = cls.OBJTYPE
        if not path:
            path = cls.PATH
        if not query:
            query = kwargs
        return objtype.db(path).find(query).count()
    
    @classmethod
    def get_last(cls, **kwargs):
        """
        Gets the last item from a collection, returning a DatabaseObject.
        This is primarily for collections that use random_id's, as mongo's id's
        are in alphachronological order (alphabetical order of time), and this
        will return the most recent item in that case.
        
        @param **kwargs: forwarded to cls.__init__
        """
        try:
            return cls(page_size=1, ascending=False, **kwargs)[0]
        except IndexError:
            return None
    
    @classmethod
    def iterator(cls, path=None, objtype=None, query=None, page_size=1000, **kwargs):
        """"
        Linear time, constant memory, iterator for a mongo collection.
        
        @param path: the path of the database to query, in the form
            "database.colletion"; pass None to use the value of the
            PATH property of the object or, if that is none, the
            PATH property of OBJTYPE
        @param objtype: the object type to use for these DatabaseObjects;
            pass None to use the OBJTYPE property of the class
        @param query: a dictionary specifying key-value pairs that the result
            must match.  If query is None, use kwargs in it's place
        @param page_size: the number of items to fetch per page of iteration
        @param **kwargs: used as query parameters if query is None
        """
        if not objtype:
            objtype = cls.OBJTYPE
        if not path:
            path = cls.PATH
        db = objtype.db(path)
        if not query:
            query = kwargs
        results = list(db.find(query).sort(ID_KEY, ASCENDING).limit(page_size))
        while results:
            page = [objtype(path=path, _new_object=result) for result in results]
            for obj in page:
                yield obj
            query[ID_KEY] = {GT: results[-1][ID_KEY]}
            results = list(db.find(query).sort(ID_KEY, ASCENDING).limit(page_size))
    
    def db(self):
        """
        Calls the db method of OBJTYPE
        
        NOTE: this function is only properly usable on children classes that
        have overridden either OBJTYPE or PATH
        
        @raise Exception: if self.OBJTYPE.PATH or path are valid
        """
        return self.OBJTYPE.db(self.PATH)
    
    def insert(self, data, **kwargs):
        """
        Calls the create method of OBJTYPE
        
        NOTE: this function is only properly usable on children classes that
        have overridden either OBJTYPE or PATH.
        
        @param data: the data of the new object to be created
        @param **kwargs: forwarded to create
        
        @raise DatabaseConflictError: if there is already an object with that
            ID_KEY and overwrite == False
        @raise MalformedObjectError: if a REQUIRED key of defaults is missing,
            or if the ID_KEY of the object is None and random_id is False
        """
        obj = self.OBJTYPE.create(data, path=self.PATH, **kwargs)
        self.append(obj)
        return obj
    
    def to_json(self):
        """
        Returns the json string of the database collection in utf-8.
        
        Note: ObjectId and datetime.datetime objects are custom-serialized
        using the MongoliaJSONEncoder because they are not natively json-
        serializable.
        """
        return json.dumps(self, cls=MongoliaJSONEncoder, encoding="utf-8")
    
    def _move(self, new_path):
        """
        Moves the collection to a different database path
        
        NOTE: this function is intended for command prompt use only.
        
        WARNING: if execution is interrupted halfway through, the collection will
        be split into multiple pieces.  Furthermore, there is a possible
        duplication of the database object being processed at the time of
        interruption.
        
        @param new_path: the new place for the collection to live, in the format
            "database.collection"
        """
        for elt in self:
            DatabaseObject.create(elt, path=new_path)
        for elt in self:
            elt._collection.remove({ID_KEY: elt[ID_KEY]})
