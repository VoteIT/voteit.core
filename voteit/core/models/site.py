import colander
from repoze.who.plugins.zodb.users import Users

from voteit.core.models.base_content import BaseContent


class SiteRoot(BaseContent):
    """ The root of the site. Contains all other objects. """
    
    content_type = 'SiteRoot'

    omit_fields_on_edit = ['name']
    allowed_contexts = []
    
    @property
    def users(self):
        """ Contains all users. user_id should be the same as set name."""
        users = getattr(self, '__users__', None)
        if users is None:
            users = self.__users__ = Users()
        return users

#    @property
#    def groups(self):
#        """ Contains all groups. """
#        groups = getattr(self, '__groups__', None)
#        if groups is None:
#            groups = self.__groups__ = Folder()
#        return groups


class SiteRootSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
