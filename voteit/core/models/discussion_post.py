from __future__ import unicode_literals
import re

from BTrees.OOBTree import OOBTree
from arche.security import get_acl_registry
from pyramid.traversal import find_interface
from zope.interface import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.helpers import TAG_PATTERN
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.base_content import BaseContent
from voteit.core.models.date_time_util import utcnow


@implementer(IDiscussionPost, ICatalogMetadataEnabled)
class DiscussionPost(BaseContent):
    """ Discussion Post content type.
        See :mod:`voteit.core.models.interfaces.IDiscussionPost`.
        All methods are documented in the interface of this class.
    """
    type_name = 'DiscussionPost'
    type_title = _("Discussion Post")
    add_permission = security.ADD_DISCUSSION_POST
    custom_mutators = {'text': '_set_text',
                       'title': '_set_title',}
    custom_accessors = {'title': '_get_title',
                        'mentioned': '_get_mentioned'}

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

    #Override title, it will be used to generate a name for this content. (Like an id)
    def _get_title(self, key = None, default = u""):
        return self.get_field_value('text', default = default)

    def _set_title(self, value, key = None):
        """ Override set tilte for this content type."""
        #This has to do with b/c
        self._set_text(value, key = key)

    title = property(_get_title, _set_title)

    def _set_text(self, value, key = None):
        self.field_storage['text'] = value

    @property
    def mentioned(self):
        try:
            return self.__mentioned__
        except AttributeError:
            self.__mentioned__ = OOBTree()
            return self.__mentioned__

    def add_mention(self, userid):
        self.mentioned[userid] = utcnow()

    def get_tags(self, default = ()):
        tags = []
        for matchobj in re.finditer(TAG_PATTERN, self.get_field_value('text', '')):
            tag = matchobj.group('tag').lower()
            if tag not in tags:
                tags.append(tag)
        return tags and tags or default


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
