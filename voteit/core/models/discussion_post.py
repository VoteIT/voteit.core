from __future__ import unicode_literals

from arche.security import get_acl_registry
from pyramid.traversal import find_interface
from zope.interface import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.helpers import strip_and_truncate
from voteit.core.helpers import tags_from_text
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.base_content import BaseContent


@implementer(IDiscussionPost, ICatalogMetadataEnabled)
class DiscussionPost(BaseContent):
    """ Discussion Post content type.
        See :mod:`voteit.core.models.interfaces.IDiscussionPost`.
        All methods are documented in the interface of this class.
    """
    type_name = 'DiscussionPost'
    type_title = _("Discussion Post")
    add_permission = security.ADD_DISCUSSION_POST

    @property
    def __acl__(self):
        meeting = find_interface(self, IMeeting)
        acl = get_acl_registry()
        if meeting.get_workflow_state() == 'closed':
            return acl.get_acl('DiscussionPost:closed')
        ai = find_interface(self, IAgendaItem)
        ai_state = ai.get_workflow_state()
        #If ai is private, use private
        if ai_state == 'private':
            return acl.get_acl('DiscussionPost:private')
        return acl.get_acl('DiscussionPost:open')

    @property
    def title(self):
        return strip_and_truncate(self.text, limit = 100, symbol = '')
    @title.setter
    def title(self, value):
        raise NotImplementedError("Tried to set title on DiscussionPost")

    @property
    def text(self):
        return self.get_field_value('text', '')
    @text.setter
    def text(self, value):
        self.set_field_value('text', value)

    @property
    def tags(self): #arche compat
        return tags_from_text(self.text)
    @tags.setter
    def tags(self, value):
        print "Tags shouldn't be set like this"


def includeme(config):
    config.add_content_factory(DiscussionPost, addable_to = 'AgendaItem')
    aclreg = config.registry.acl
    acl_open = aclreg.new_acl('DiscussionPost:open')
    acl_open.add(security.ROLE_ADMIN, (security.VIEW, security.DELETE, security.EDIT, security.MODERATE_MEETING))
    acl_open.add(security.ROLE_MODERATOR, (security.VIEW, security.DELETE, security.EDIT, security.MODERATE_MEETING))
    acl_open.add(security.ROLE_OWNER, security.DELETE)
    acl_open.add(security.ROLE_VIEWER, security.VIEW)
    acl_closed = aclreg.new_acl('DiscussionPost:closed')
    acl_closed.add(security.ROLE_ADMIN, (security.VIEW, security.MODERATE_MEETING))
    acl_closed.add(security.ROLE_MODERATOR, (security.VIEW, security.MODERATE_MEETING))
    acl_closed.add(security.ROLE_VIEWER, security.VIEW)
    acl_private = aclreg.new_acl('DiscussionPost:private')
    acl_private.add(security.ROLE_ADMIN, (security.VIEW, security.DELETE, security.EDIT, security.MODERATE_MEETING))
    acl_private.add(security.ROLE_MODERATOR, (security.VIEW, security.DELETE, security.EDIT, security.MODERATE_MEETING))
