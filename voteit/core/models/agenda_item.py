import colander
import deform
from zope.interface import implements
from pyramid.traversal import find_interface
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


ACL = {}
ACL['private'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, security.DELETE, )),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.DELETE, )),
                  DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, )),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW, )),
                 (Allow, security.ROLE_PARTICIPANT, (security.VIEW, )),
                 (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                 DENY_ALL,
                ]


class AgendaItem(BaseContent):
    """ Agenda Item content. """
    implements(IAgendaItem)
    content_type = 'AgendaItem'
    display_name = _(u"Agenda item")
    allowed_contexts = ('Meeting',)
    add_permission = security.ADD_AGENDA_ITEM

    @property
    def __acl__(self):
        state = self.get_workflow_state
        if state == 'closed':
            return ACL['closed']
        if state == 'private':
            return ACL['private']
        
        meeting = find_interface(self, IMeeting)
        if meeting.get_workflow_state == u'closed':
            return ACL['closed']
        

        raise AttributeError("Go fetch parents acl")




def construct_schema(**kwargs):
    context = kwargs.get('context', None)
    if context is None:
        KeyError("'context' is a required keyword for Agenda Item schemas. See construct_schema in the agenda_item module.")

    #Check current ids
    current_ids = set()
    for obj in context.get_content(content_type='AgendaItem'):
        value = obj.get_field_value('agenda_item_id')
        #A '0' should be a string here so this should be okay
        if value:
            current_ids.add(value)

    #Suggest currently highetst int +1 as new id
    suggested_id = "0"
    current_numbers = set()
    for id in current_ids:
        try:
            i = int(id)
            current_numbers.add(i)
        except ValueError:
            continue
        
    if current_numbers:
        suggested_id = str(max(current_numbers)+1)

    #Internal methods
    def _validate_uniqueness_ai_id(node, value):
        """ Requires current_ids to be set. """
        if value in current_ids:
            raise colander.Invalid(node, _(u"This value isn't unique within this meeting."))

    
    class AgendaItemSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String(),
                                    title = _(u"Title"),)
        description = colander.SchemaNode(
            colander.String(),
            title = _(u"Description"),
            widget=deform.widget.TextAreaWidget(rows=10, cols=60),
        )
        agenda_item_id = colander.SchemaNode(
            colander.String(),
            title = _(u"Agenda Item ID."),
            description = _(u"Normally this will be a number. If it's an integer, "
                            "it will be used for sorting. Must be unique regardless of value."),
            default = suggested_id,
            missing = u"",
            validator = _validate_uniqueness_ai_id,
        )
    return AgendaItemSchema()


def includeme(config):
    from voteit.core import register_content_info
    register_content_info(construct_schema, AgendaItem, registry=config.registry)
