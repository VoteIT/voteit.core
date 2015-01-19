from BTrees.OOBTree import OOBTree

from arche.utils import get_content_factories


def createContent(type_name, *args, **kw):
    """ Replaces the betahaus.pyracont createContent method with a wrapper for Arches
        factory implementation.
    """
    factories = get_content_factories()
    return factories[type_name](*args, **kw)

# 
# class ArcheCompatMixin(object):
#     """ Compatibility module between VoteIT and Arche.
#         This mixin must ALWAYS have a higher priority than anything inherited from Arche
#         if it uses VoteITs storage model.
#     
#         Arche            VoteIT
#         ==================================
#         creator          creators
#         type_name        content_type
#         type_title       display_name
# 
#         Similar attributes in BaseContent:
#         uid, created, modified, description, title
#     """
#     @property
#     def creator(self):
#         return self.get_field_value('creators', ())
#     @creator.setter
#     def creator(self, value):
#         self.set_field_value('creators', value)
# 
#     @property
#     def creators(self):
#         #b/c compat
#         return self.get_field_value('creators', ())
#     @creators.setter
#     def creators(self, value):
#         self.set_field_value('creators', value)
# 
#     @property
#     def content_type(self):
#         return self.type_name
# 
#     @property
#     def display_name(self):
#         return self.type_title
