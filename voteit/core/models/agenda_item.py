import colander
import deform
from zope.interface import implements
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS

from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from pyramid.traversal import find_interface


ACL = {}
ACL['private'] = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.DELETE)),
                  DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW,)),
                 (Allow, security.ROLE_PARTICIPANT, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                 DENY_ALL,
                ]


class AgendaItem(BaseContent):
    """ Agenda Item content. """
    implements(IAgendaItem)
    content_type = 'AgendaItem'
    omit_fields_on_edit = ('name',)
    allowed_contexts = ('Meeting',)
    add_permission = security.ADD_AGENDA_ITEM

    @property
    def __acl__(self):
        state = self.get_workflow_state
        if state == 'closed':
            return ACL['closed']
        
        meeting = find_interface(self, IMeeting)
        if meeting.get_workflow_state == u'closed':
            return ACL['closed']
        
        if state == 'private':
            return ACL['private']

        raise AttributeError("Go fetch parents acl")




def construct_schema(**kwargs):
    class AgendaItemSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(
            colander.String(),
            widget=deform.widget.TextAreaWidget(rows=10, cols=60),
        )
    return AgendaItemSchema()


def includeme(config):
    from voteit.core import register_content_info
    register_content_info(construct_schema, AgendaItem, registry=config.registry)
