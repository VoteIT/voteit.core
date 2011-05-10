from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IVote
from voteit.core import security


class Vote(BaseContent):
    """ Vote content. This is not addable through regular content factories.
        It's used as a storage for a users vote by a vote plugin.
    """
    implements(IVote)
    
    content_type = 'Vote'
    omit_fields_on_edit = ()
    allowed_contexts = () #N/A for this content type, it shouldn't be addable the normal way.

    #FIXME: ACL need to reflect workflow
    __acl__ = [(Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW,)),
               DENY_ALL,
               ]

    def set_vote_data(self, value):
        """ Set vote data """
        self.__vote_data__ = value
    
    def get_vote_data(self):
        """ Get vote data. """
        return getattr(self, '__vote_data__', None)
