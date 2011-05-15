from repoze.folder import Folder
from zope.interface import implements
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import IContentTypeInfo
from voteit.core.models.content_type_info import ContentTypeInfo


class ContentUtility(Folder):
    """ See IContentUtility """
    implements(IContentUtility)
    
    def add(self, factory_obj, verify=True):
        """ See IContentUtility. """
        if verify:
            verifyObject(IContentTypeInfo, factory_obj)
        
        name = str(factory_obj.content_type)
        super(ContentUtility, self).add(name, factory_obj)

    def create(self, schema, type_class, update_method=None):
        """ See IContentUtility. """
        return ContentTypeInfo(schema, type_class, update_method=update_method)

    def addable_in_type(self, content_type):
        """ See IContentUtility. """
        result = set()
        for type in self.values():
            if content_type in type.allowed_contexts:
                result.add(type)
        return frozenset(result)
