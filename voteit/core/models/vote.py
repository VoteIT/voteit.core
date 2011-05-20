from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IVote

ACL = {}
ACL['ongoing'] = [(Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.DELETE,)),
                  DENY_ALL,
                  ]
ACL['closed'] = [(Allow, security.ROLE_OWNER,  security.VIEW,),
                  DENY_ALL,
                  ]


class Vote(BaseContent):
    """ Vote content. This is not addable through regular content factories.
        It's used as a storage for a users vote by a vote plugin.
    """
    implements(IVote)
    
    content_type = 'Vote'
    omit_fields_on_edit = ()
    allowed_contexts = () #N/A for this content type, it shouldn't be addable the normal way.
    add_permission = security.ADD_VOTE
    
    title = _(u"Your vote")
    description = _(u"This is your vote. While the poll is open, you can delete or change it if you wish.")

    @property
    def __acl__(self):
        poll = find_interface(self, IPoll)
        state = poll.get_workflow_state
        if state == 'ongoing':
            return ACL['ongoing']
        return ACL['closed']

    def set_vote_data(self, value):
        """ Set vote data """
        self.__vote_data__ = value
    
    def get_vote_data(self):
        """ Get vote data. """
        return getattr(self, '__vote_data__', None)
