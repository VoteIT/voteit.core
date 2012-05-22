import colander
import deform
from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface
from betahaus.pyracont.decorators import content_factory
from webhelpers.html.tools import auto_link
from webhelpers.html.converters import nl2br

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.base_content import BaseContent


ACL =  {}
ACL['open'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_MODERATOR, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_OWNER, (security.DELETE, )),
               (Allow, security.ROLE_VIEWER, (security.VIEW,)),
               DENY_ALL,
               ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, security.VIEW),
                 (Allow, security.ROLE_MODERATOR, security.VIEW),
                 (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                 DENY_ALL,
                ]
ACL['private'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.DELETE, )),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.DELETE, )),
                  DENY_ALL,
                  ]

@content_factory('DiscussionPost', title=_(u"Discussion Post"))
class DiscussionPost(BaseContent):
    """ Discussion Post content type.
        See :mod:`voteit.core.models.interfaces.IDiscussionPost`.
        All methods are documented in the interface of this class.
    """
    implements(IDiscussionPost, ICatalogMetadataEnabled)
    content_type = 'DiscussionPost'
    display_name = _(u"Discussion Post")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_DISCUSSION_POST
    schemas = {'add': 'DiscussionPostSchema'}
    custom_mutators = {'text': '_set_text',
                       'title': '_set_title'}
    custom_accessors = {'title': '_get_title'}

    @property
    def __acl__(self):
        meeting = find_interface(self, IMeeting)
        if meeting.get_workflow_state() == 'closed':
            return ACL['closed']
        ai = find_interface(self, IAgendaItem)
        ai_state = ai.get_workflow_state()
        #If ai is private, use private
        if ai_state == 'private':
            return ACL['private']
        return ACL['open']

    #Override title, it will be used to generate a name for this content. (Like an id)
    def _get_title(self, key = None, default = u""):
        return self.get_field_value('text', default = default)

    def _set_title(self, value, key = None):
        """ Override set tilte for this content type."""
        #This has to do with b/c
        self._set_text(value, key = key)

    title = property(_get_title, _set_title)

    def _set_text(self, value, key = None):
        """ Custom mutator, will transform urls to links and linebreaks to <br/> """
        value = auto_link(value)
        value = nl2br(value)
        #nl2br will also ad a \n to the end, we need to remove it so it doesn't run several times
        value = value.replace('\n', ' ')
        self.field_storage['text'] = value
