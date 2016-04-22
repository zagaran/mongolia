import datetime
import dateutil
import json
from bson import ObjectId


OBJECTID_IDENTIFIER = "$oid"
ISO_8601_IDENTIFIER = "$iso"

class MongoliaJSONEncoder(json.JSONEncoder):
    """
    Adds the ability to serialize python ObjectId and datetime.datetime objects
    when included in json.dumps(). The results are json objects with their
    respective identifiers as keys and their serialized values as values.
    
    ObjectId objects are serialized as strings, and datetime.datetime objects
    are serialized to the standard ISO 8601 format.
    
    >>> json.dumps(ObjectId('5717fc0d78ba2f1d6c41919a'), cls=MongoliaJSONEncoder)
    '{OBJECTID_IDENTIFIER: "5717fc0d78ba2f1d6c41919a"}'
    
    >>> json.dumps(datetime.datetime(2016, 4, 20, 18, 28, 12), cls=MongoliaJSONEncoder)
    '{ISO_8601_IDENTIFIER: "2016-04-20T18:28:12"}'
    """
    def default(self, o):
        if isinstance(o, ObjectId):
            return {
                OBJECTID_IDENTIFIER: str(o)
            }
        if isinstance(o, datetime.date) or isinstance(o, datetime.datetime):
            return {
                ISO_8601_IDENTIFIER: o.isoformat()
            }
        return super(MongoliaJSONEncoder, self).default(o)


class MongoliaJSONDecoder(json.JSONDecoder):
    """
    Adds the ability to deserialize Mongolia's json representations of python
    ObjectId and datetime.datetime objects when included in json.loads().
    
    >>> json.loads('{OBJECTID_IDENTIFIER: "5717fc0d78ba2f1d6c41919a"}', cls=MongoliaJSONDecoder)
    ObjectId('5717fc0d78ba2f1d6c41919a')
    
    >>> json.loads('{ISO_8601_IDENTIFIER: "2016-04-20T18:28:12"}', cls=MongoliaJSONDecoder)
    datetime.datetime(2016, 4, 20, 18, 28, 12)
    """
    def __init__(self, *args, **kwargs):
        super(MongoliaJSONDecoder, self).__init__(object_hook=self.convert, *args, **kwargs)
    
    def convert(self, o):
        if OBJECTID_IDENTIFIER in o:
            return ObjectId(o[OBJECTID_IDENTIFIER])
        if ISO_8601_IDENTIFIER in o:
            return dateutil.parser.parse(o[ISO_8601_IDENTIFIER])
        return o