import abc

from blitzdb.document import Document
from blitzdb.backends.base import Backend as BaseBackend
from blitzdb.backends.mongo.queryset import QuerySet
import uuid

class Backend(BaseBackend):

    """
    """

    class Meta(BaseBackend.Meta):
        supports_indexes = True
        supports_transactions = False

    def __init__(self,db,**kwargs):
        self.db = db
        self.classes = {}
        self.collections = {}
        super(Backend,self).__init__(**kwargs)

    def begin(self):
        """
        Starts a new transaction
        """
        pass

    def rollback(self):
        """
        Rolls back a transaction
        """
        pass

    def commit(self):
        """
        Commits a transaction
        """
        pass

    def get(self,cls_or_collection,properties):
        if not isinstance(cls_or_collection,str) and not isinstance(cls_or_collection,unicode):
            collection = self.get_collection_for_cls(cls_or_collection)
        else:
            collection = cls_or_collection
        attributes = self.db[collection].find_one(self.serialize(properties,convert_keys_to_str = True))
        cls = self.get_cls_for_collection(collection)
        if not attributes:
            raise cls.DoesNotExist
        return self.create_instance(cls,self.deserialize(attributes))

    def delete(self,obj):
        collection = self.get_collection_for_cls(obj.__class__)
        if obj.pk == None:
            raise obj.DoesNotExist
        self.db[collection].remove({'_id' : obj.pk})

    def save(self,obj):
        collection = self.get_collection_for_cls(obj.__class__)
        if obj.pk == None:
            obj.pk = uuid.uuid4().hex
        serialized_attributes = self.serialize(obj.attributes,convert_keys_to_str = True)
        serialized_attributes['_id'] = obj.pk
        self.db[collection].save(serialized_attributes)

    def create_index(self,cls_or_collection,*args,**kwargs):
        if not isinstance(cls_or_collection,str) and not isinstance(cls_or_collection,unicode):
            collection = self.get_collection_for_cls(cls_or_collection)
        else:
            collection = cls_or_collection
        self.db[collection].ensure_index(*args,**kwargs)

    def compile_query(self,query):
        if isinstance(query,dict):
            return dict([(self.compile_query(key),self.compile_query(value)) for key,value in query.items()])
        elif isinstance(query,list):
            return {'$all' : [self.compile_query(x) for x in query]}
        else:
            return self.serialize(query,convert_keys_to_str = True)

    def filter(self,cls_or_collection,query,sort_by = None,limit = None,offset = None):

        if not isinstance(cls_or_collection,str) and not isinstance(cls_or_collection,unicode):
            collection = self.get_collection_for_cls(cls_or_collection)
            cls = cls_or_collection
        else:
            collection = cls_or_collection
            cls = self.get_cls_for_collection(collection)

        compiled_query = self.compile_query(query)

        return QuerySet(self,cls,self.db[collection].find(compiled_query))