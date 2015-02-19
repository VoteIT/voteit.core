from __future__ import unicode_literals

#from zope.interface import implementsOnly
from pyramid.traversal import find_interface
#from betahaus.pyracont.decorators import content_factory
from zope.component.event import objectEventNotify
from zope.interface import implementer_only
from arche.interfaces import ILocalRoles
from arche.security import get_acl_registry

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IVote
from voteit.core.events import ObjectUpdatedEvent


#@content_factory('Vote', title=_(u"Vote"))
@implementer_only(IVote, ILocalRoles) #This blanks out other interfaces!
class Vote(BaseContent):
    """ Vote content type.
        See :mod:`voteit.core.models.interfaces.IVote`.
        All methods are documented in the interface of this class.
    """
    type_name = 'Vote'
    type_title = _("Vote")
    add_permission = security.ADD_VOTE

    @property
    def __acl__(self):
        poll = find_interface(self, IPoll)
        state = poll.get_workflow_state()
        acl = get_acl_registry()
        if state == 'ongoing':
            return acl.get_acl('Vote:ongoing')
        return acl.get_acl('Vote:closed')

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

def includeme(config):
    config.add_content_factory(Vote)
    aclreg = config.registry.acl
    ongoing = aclreg.new_acl('Vote:ongoing')
    ongoing.add(security.ROLE_OWNER, (security.EDIT, security.VIEW, security.DELETE,))
    closed = aclreg.new_acl('Vote:closed')
    closed.add(security.ROLE_OWNER, security.VIEW)
