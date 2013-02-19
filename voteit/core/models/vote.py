from zope.interface import implementsOnly
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface
from betahaus.pyracont.decorators import content_factory
from zope.component.event import objectEventNotify

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IVote
from voteit.core.events import ObjectUpdatedEvent


ACL = {}
ACL['ongoing'] = [(Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.DELETE,)),
                  DENY_ALL,
                  ]
ACL['closed'] = [(Allow, security.ROLE_OWNER,  security.VIEW,),
                  DENY_ALL,
                  ]


@content_factory('Vote', title=_(u"Vote"))
class Vote(BaseContent):
    """ Vote content type.
        See :mod:`voteit.core.models.interfaces.IVote`.
        All methods are documented in the interface of this class.
    """
    implementsOnly(IVote) #This blanks out other interfaces!
    content_type = 'Vote'
    display_name = _(u"Vote")
    allowed_contexts = () #N/A for this content type, it shouldn't be addable the normal way.
    add_permission = security.ADD_VOTE
    
    title = _(u"Your vote")
    description = _(u'your_vote_description',
                    default = _(u"This is your vote. While the poll is open, you can delete or change it if you wish."))

    @property
    def __acl__(self):
        poll = find_interface(self, IPoll)
        state = poll.get_workflow_state()
        if state == 'ongoing':
            return ACL['ongoing']
        return ACL['closed']

    def get_vote_data(self, default = None):
        """ Get vote data. """
        return getattr(self, '__vote_data__', default)

    def set_vote_data(self, value, notify = True):
        """ Set vote data """
        marker = object()
        current_val = self.get_vote_data(marker)
        if value == current_val:
            return
        self.__vote_data__ = value
        if notify:
            objectEventNotify(ObjectUpdatedEvent(self))
