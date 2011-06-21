
import colander
from zope.interface import implements

from repoze.folder.interfaces import IObjectAddedEvent
from pyramid.security import Allow, DENY_ALL
from pyramid.events import subscriber

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.base_content import BaseContent
from voteit.core.validators import html_string_validator

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


class DiscussionPost(BaseContent):
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


#@subscriber(IDiscussionPost, IObjectAddedEvent)
#def discussion_post_added(obj, event):
#    """ Callback for when an object is added. This is used to do extra things,
#        like adding hashtags, mentions, notifying users etc.
#    """
    #FIXME: implement


def construct_schema(**kwargs):
    class Schema(colander.Schema):
        text = colander.SchemaNode(colander.String(),
                                    title = _(u"Text"),
                                    validator=html_string_validator,)
    return Schema()


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, DiscussionPost, registry=config.registry)
