from zope.interface import implements
from voteit.core.models.interfaces import IContentTypeInfo


class ContentTypeInfo(object):
    """ schema: add schema for the content type.
        type_class: which class the content type is constructed from.
        allowed_contexts: which contexts this type can be added to.
        add_permission: which permission is required to add.
        
        Any assignment that is None means None, which would mean that
        most types wouldn't be addable.
    """
    implements(IContentTypeInfo)
    
    def __init__(self, schema, type_class):
        self.schema = schema
        self.type_class = type_class

    @property
    def content_type(self):
        return self.type_class.content_type
    
    @property
    def allowed_contexts(self):
        return self.type_class.allowed_contexts

    @property
    def add_permission(self):
        return self.type_class.add_permission