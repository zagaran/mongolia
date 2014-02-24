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

from pymongo import MongoClient
from pymongo.errors import AutoReconnect, ConnectionFailure
from mongolia.errors import DatabaseIsDownError


class AlertLevel(object):
    """ Options for the argument of set_defaults_handling """
    
    error = "error"
    warning = "warning"
    none = None

class MongoConnection(object):
    """
    MongoConnecton is an object that lazily loads a pymongo.MongoClient;
    the MongoClient is not actually initialized until the user gets it the first
    time through get_connection, explicitly connects to it through connect,
    or authenticates it through authenticate.
    """
    __connection = None
    default_handling = AlertLevel.none
    
    def get_connection(self):
        """ Returns the the current MongoClient,
            or creates a new one if there isn't one yet"""
        if self.__connection is None:
            self.connect()
        return self.__connection
    
    def connect(self, host=None, port=None, **kwargs):
        """ Explicitly creates the MongoClient; this method must be used
            in order to specify a non-default host or port to the MongoClient.
            Takes arguments identical to MongoClient.__init__"""
        try:
            self.__connection = MongoClient(host=host, port=port, **kwargs)
        except (AutoReconnect, ConnectionFailure):
            raise DatabaseIsDownError("No mongod process is running.")
    
    def authenticate(self, username, password, db=None):
        """ Authenticates the MongoClient with the passed username and password """
        if db is None:
            return self.get_connection().admin.authenticate(username, password)
        return self.get_connection()[db].authenticate(username, password)
    
    def add_user(self, name, password=None, read_only=None, db=None, **kwargs):
        """ Adds a user that can be used for authentication """
        if db is None:
            return self.get_connection().admin.add_user(
                    name, password=password, read_only=read_only, **kwargs)
        return self.get_connection()[db].add_user(
                    name, password=password, read_only=read_only, **kwargs)

# TODO: allow multiple simultaneous connections
CONNECTION = MongoConnection()


def connect_to_database(host=None, port=None, **kwargs):
    """
    Explicitly begins a database connection for the application
    (if this function is not called, a connection is created when
    it is first needed).  Takes arguments identical to
    pymongo.MongoClient.__init__
    
    @param host: the hostname to connect to
    @param port: the port to connect to
    """
    return CONNECTION.connect(host=host, port=port, **kwargs)

def authenticate_connection(username, password, db=None):
    """
    Authenticates the current database connection with the passed username
    and password.  If the database connection uses all default parameters,
    this can be called without connect_to_database.  Otherwise, it should
    be preceded by a connect_to_database call.
    
    @param username: the username with which you authenticate; must match
        a user registered in the database
    @param password: the password of that user
    @param db: the database the user is authenticated to access.  Passing None
    (the default) means authenticating against the admin database, which
    gives the connection access to all databases
    
    Example; connecting to all databases locally:
        connect_to_database()
        authenticate_connection("username", "password")
    
    Example; connecting to a particular database of a remote server:
        connect_to_database(host="example.com", port="12345")
        authenticate_connection("username", "password", db="somedb")
    
    """
    return CONNECTION.authenticate(username, password, db=db)

def set_defaults_handling(alert_level):
    """
    When DEFAULTS have been specified for a DatabaseObject and a key not in
    the specified DEFAULTS is modified, there are three options, detailed below.
    This function sets the behavior globally for the active system.
    
    @param alert_level: this parameter takes one of three options:
        AlertLevel.error: raises an InvalidKeyError if a non-default key is set.
            Use this option if you are using DEFAULTS as strict database
            schemas, and only things in DEFAULTS should appear in the database.
        AlertLevel.warning (default): prints a warning if a non-default key is
            set.  Use this option if you are using DEFAULTS as strict database
            schemas, but data should still be stored in the event of a mismatch.
        AlertLevel.none: does nothing if a non-default key is set.  Use this
            option if you are just using DEFAULTS to populate default values
            and not as strict database schemas.
    """
    CONNECTION.defaults_handling = alert_level

def add_user(name, password=None, read_only=None, db=None, **kwargs):
    """
    Adds a user that can be used for authentication.
    
    @param name: the name of the user to create
    @param passowrd: the password of the user to create. Can not be used with
        the userSource argument.
    @param read_only: if True the user will be read only
    @param db: the database the user is authenticated to access.  Passing None
        (the default) means add the user to the admin database, which gives the
        user access to all databases
    @param **kwargs: forwarded to pymongo.database.add_user
    
    Example; adding a user with full database access:
        add_user("username", "password")
    
    Example; adding a user with read only privilage on a partiucalr database:
        add_user("username", "password", read_only=True, db="somedb")
    
    NOTE: This function will only work if mongo is being run unauthenticated
    or you have already authenticated with another user with appropriate
    privileges to add a user to the specified database.
    """
    return CONNECTION.add_user(name, password=password, read_only=read_only, db=db, **kwargs)

def list_database(db=None):
    """
    Lists the names of either the databases on the machine or the collections
    of a particular database
    
    @param db: the database for which to list the collection names;
        if db is None, then it lists all databases instead
        the contents of the database with the name passed in db
    """
    if db is None:
        return CONNECTION.get_connection().database_names()
    return CONNECTION.get_connection()[db].collection_names()
