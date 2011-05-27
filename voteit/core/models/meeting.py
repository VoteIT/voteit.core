import colander
import deform
from zope.interface import implements
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS, Authenticated

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core import register_content_info
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


ACL = {}
ACL['default'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, security.MANAGE_GROUPS, security.DELETE, )),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.MANAGE_GROUPS, security.DELETE, )),
                  (Allow, security.ROLE_OWNER, (security.VIEW, security.EDIT, security.DELETE, )),
                  (Allow, security.ROLE_PARTICIPANT, (security.VIEW, security.ADD_PROPOSAL, )),
                  (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                  (Allow, Authenticated, security.REQUEST_MEETING_ACCESS),
                  DENY_ALL,
                   ]
ACL['private'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, security.MANAGE_GROUPS, security.DELETE, )),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.MANAGE_GROUPS, security.DELETE, )),
                  DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.MANAGE_GROUPS, )),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW, security.MANAGE_GROUPS, )),
                 (Allow, security.ROLE_OWNER, (security.VIEW, )),
                 (Allow, security.ROLE_PARTICIPANT, (security.VIEW, )),
                 (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                 DENY_ALL,
                ]


class Meeting(BaseContent):
    """ Meeting content. """
    implements(IMeeting)
    content_type = 'Meeting'
    display_name = _(u"Meeting")
    allowed_contexts = ('SiteRoot',)
    add_permission = security.ADD_MEETING

    @property
    def __acl__(self):
        return ACL.get(self.get_workflow_state, ACL['default'])


def construct_schema(**kwargs):
    if kwargs.get('type') == 'request_access':
        class RequestAccessSchema(colander.Schema):
            message = colander.SchemaNode(colander.String(),
                                          title = _(u"Message"),
                                          validator = colander.Length(5, 999),
                                          default = _(u"Knock knock - Please let me access the meeting."),
                                          widget = deform.widget.TextAreaWidget(rows=5, cols=40),)
        return RequestAccessSchema()
    
    #Default schema
    class MeetingSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(
            colander.String(),
            widget=deform.widget.TextAreaWidget(rows=10, cols=60))
    return MeetingSchema()

def includeme(config):
    register_content_info(construct_schema, Meeting, registry=config.registry)
