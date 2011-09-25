import colander
import deform
from zope.interface import implements
from pyramid.traversal import find_interface
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS
from pyramid.threadlocal import get_current_request
from zope.component import getUtility

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.validators import html_string_validator
from voteit.core.fields import TZDateTime


_PRIV_MOD_PERMS = (security.VIEW, security.EDIT, security.DELETE, security.MODERATE_MEETING, security.CHANGE_WORKFLOW_STATE, )

ACL = {}
ACL['private'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, _PRIV_MOD_PERMS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, _PRIV_MOD_PERMS),
                  DENY_ALL,
                ]
ACL['closed_ai'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.CHANGE_WORKFLOW_STATE,
                                                  security.ADD_DISCUSSION_POST, security.MODERATE_MEETING, )),
                    (Allow, security.ROLE_MODERATOR, (security.VIEW, security.CHANGE_WORKFLOW_STATE,
                                                      security.ADD_DISCUSSION_POST, security.MODERATE_MEETING, )),
                    (Allow, security.ROLE_PARTICIPANT, (security.VIEW, security.ADD_DISCUSSION_POST, )),
                    (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                    DENY_ALL,
                   ]
ACL['closed_meeting'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, )),
                         (Allow, security.ROLE_MODERATOR, (security.VIEW, )),
                         (Allow, security.ROLE_PARTICIPANT, (security.VIEW, )),
                         (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                         DENY_ALL,
                        ]


class AgendaItem(BaseContent, WorkflowAware):
    """ Agenda Item content. """
    implements(IAgendaItem, ICatalogMetadataEnabled)
    content_type = 'AgendaItem'
    display_name = _(u"Agenda item")
    allowed_contexts = ('Meeting',)
    add_permission = security.ADD_AGENDA_ITEM

    @property
    def __acl__(self):
        state = self.get_workflow_state()
        if state == 'closed':
            #Check if the meeting is closed, if not discussion should be allowed +
            #it should be allowed to change the workflow back
            if self.__parent__.get_workflow_state() == 'closed':
                return ACL['closed_meeting']
            return ACL['closed_ai']
        if state == 'private':
            return ACL['private']

        raise AttributeError("Go fetch parents acl")

    @property
    def agenda_item_id(self):
        return self.get_field_value('agenda_item_id')

    @property
    def start_time(self):
        return self.get_field_value('start_time')

    @property
    def end_time(self):
        return self.get_field_value('end_time')

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

    dt_util = getUtility(IDateTimeUtil)
    local_tz = dt_util.timezone
        

    class AgendaItemSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String(),
            title = _(u"Title"),
            validator=html_string_validator,
        )
        description = colander.SchemaNode(
            colander.String(),
            title = _(u"Description"),
            missing = u"",
            widget=deform.widget.RichTextWidget(),
        )
        summary = colander.SchemaNode(
            colander.String(),
            title = _(u"Summary of this item."),
            description = _('ai_summary_description',
                            default=u"This could be what was decided. It will show up in the log on the meeting page."),
            widget=deform.widget.TextAreaWidget(rows=10, cols=60),
            missing = u"",
            validator=html_string_validator,
        )
        start_time = colander.SchemaNode(
            TZDateTime(local_tz),
            title = _('ai_start_time_title',
                      default=u"Estimated start time of this Agenda Item."),
            description = _('ai_start_time_description',
                            default=u"No action will be taken automatically when the time has passed, so you need to open this item yourself."),
            widget=deform.widget.DateTimeInputWidget(options={'timeFormat': 'hh:mm'}),
            missing = None,
        )
        #End-time is handled by a subscriber when it is closed
    return AgendaItemSchema()


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, AgendaItem, registry=config.registry)


def closing_agenda_item_callback(context, info):
    """ Callback for workflow action. When an agenda item is closed,
        all contained proposals that haven't been handled should be set to
        "unhandled".
        If there are any open polls, this should raise an exception or an error message of some sort.
    """
    request = get_current_request() #Should be okay to use here since this method is called very seldom.
    #get_content returns a generator. It's "True" even if it's empty!
    if tuple(context.get_content(iface=IPoll, states='ongoing')):
        raise Exception("You can't close an agenda item that has ongoing polls in it. Close the polls first!")
    for proposal in context.get_content(iface=IProposal, states='published'):
        proposal.set_workflow_state(request, 'unhandled')
