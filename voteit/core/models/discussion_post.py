
import colander
import deform
from zope.interface import implements

from repoze.folder.interfaces import IObjectAddedEvent
from pyramid.security import Allow, DENY_ALL
from pyramid.events import subscriber
from pyramid.traversal import find_root

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.base_content import BaseContent
from voteit.core.models.unread_aware import UnreadAware
from voteit.core.validators import html_string_validator
from voteit.core.validators import at_userid_validator

ACL =  {}
ACL['open'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_MODERATOR, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_OWNER, (security.VIEW, security.DELETE, )),
               (Allow, security.ROLE_PARTICIPANT, (security.VIEW,)),
               (Allow, security.ROLE_VIEWER, (security.VIEW,)),
               DENY_ALL,
               ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, security.VIEW),
                 (Allow, security.ROLE_MODERATOR, security.VIEW),
                 (Allow, security.ROLE_OWNER, security.VIEW),
                 (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                 (Allow, security.ROLE_VIEWER, security.VIEW),
                 DENY_ALL,
                ]


class DiscussionPost(BaseContent, UnreadAware):
    """ Discussion post content
    """
    implements(IDiscussionPost, ICatalogMetadataEnabled)
    content_type = 'DiscussionPost'
    display_name = _(u"Discussion Post")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_DISCUSSION_POST


    @property
    def __acl__(self):
        #FIXME: Check meeting etc
        return ACL['open']

    #Override title, it will be used to generate a name for this content. (Like an id)
    def _get_title(self):
        return self.get_field_value('text')

    def _set_title(self, value):
        pass #Not used

    title = property(_get_title, _set_title)


def construct_schema(context=None, **kwargs):
    if context is None:
        KeyError("'context' is a required keyword for Discussion Post schemas. See construct_schema in the discussion post module.")
        
    root = find_root(context)
    def _at_userid_validator(node, value):
        at_userid_validator(node, value, root.users)

    class Schema(colander.Schema):
        text = colander.SchemaNode(colander.String(),
                                    title = _(u"Text"),
                                    validator=colander.All(html_string_validator, _at_userid_validator),
                                    widget=deform.widget.TextAreaWidget(rows=3, cols=40),)
    return Schema()


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, DiscussionPost, registry=config.registry)
