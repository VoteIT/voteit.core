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
    def start_time(self):
        return self.get_field_value('start_time')

    @property
    def end_time(self):
        return self.get_field_value('end_time')

def construct_schema(**kwargs):
    context = kwargs.get('context', None)
    if context is None:
        KeyError("'context' is a required keyword for Agenda Item schemas. See construct_schema in the agenda_item module.")

    dt_util = getUtility(IDateTimeUtil)
    local_tz = dt_util.timezone


    class AgendaItemSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String(),
            title = _(u"Title"),
            description = _(u"Avoid a title with more than 20 characters"),
            validator=html_string_validator,
        )
        description = colander.SchemaNode(
            colander.String(),
            title = _(u"Description"),
            description = _(u"agenda_item_description_description",
                            default=u"Place the the agenda item background information here. You can link to external documents and memos. It's also a good idea to add an image, it will make it easier for participants to quickly see which page they're on."),
            missing = u"",
            widget=deform.widget.RichTextWidget(),
        )
        summary = colander.SchemaNode(
            colander.String(),
            title = _(u"Summary of this item."),
            description = _(u"agenda_item_summary_description",
                            default=u"This summary shows up to the right on the meetings first page. Write a short summary on what is going on or what has been decided. This should be updated as the meeting progresses."),
            #description = _('ai_summary_description',
            #                default=u"This could be what was decided. It will show up in the log on the meeting page."),
            widget=deform.widget.TextAreaWidget(rows=10, cols=60),
            missing = u"",
            validator=html_string_validator,
        )
        start_time = colander.SchemaNode(
            TZDateTime(local_tz),
            title = _('ai_start_time_title',
                      default=u"Estimated start time of this Agenda Item."),
            description = _(u"agenda_item_start_time_description",
                            default=u"This setting only sets the order for the agenda item's in the Agenda. You will still have to change the state of the agenda item manually with the gear beside it's name."),
            #description = _('ai_start_time_description',
            #                default=u"No action will be taken automatically when the time has passed, so you need to open this item yourself."),
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
       

def ongoing_agenda_item_callback(context, info):
    """ Callback for workflow action. An agenda item can't be set as ongoing when meeting is not ongoing
    """
    meeting = find_interface(context, IMeeting)
    if meeting and meeting.get_workflow_state() != 'ongoing':
        raise Exception("You can't set an agenda item to ongoing if the meeting is not ongoing")
