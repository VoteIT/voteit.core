import colander
from zope.interface import implements
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS

from voteit.core import security
from voteit.core import register_content_info
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IMeeting

ACL = {}
ACL['default'] = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.MANAGE_GROUPS, security.DELETE)),
                  (Allow, security.ROLE_OWNER, (security.VIEW, security.EDIT,)),
                  (Allow, security.ROLE_PARTICIPANT, (security.VIEW, security.ADD_PROPOSAL,)),
                  (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                  DENY_ALL,
                   ]
ACL['private'] = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.MANAGE_GROUPS, security.DELETE)),
                  DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW,)),
                 (Allow, security.ROLE_PARTICIPANT, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                 DENY_ALL,
                ]


class Meeting(BaseContent):
    """ Meeting content. """
    implements(IMeeting)
    content_type = 'Meeting'
    omit_fields_on_edit = ('name',)
    allowed_contexts = ('SiteRoot',)
    add_permission = security.ADD_MEETING

    @property
    def __acl__(self):
        return ACL.get(self.get_workflow_state, ACL['default'])

    @property
    def is_closed(self):
        """ Check if the meeting is closed. After a meeting has closed,
            no one should be albe to make any changes.
        """
        return self.get_workflow_state == u'closed'


def construct_schema(**kwargs):
    class MeetingSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(colander.String())
    return MeetingSchema()

def includeme(config):
    register_content_info(construct_schema, Meeting, registry=config.registry)
