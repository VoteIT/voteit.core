import colander
import deform
from zope.interface import implements
from pyramid.traversal import find_interface, find_root
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS
from BTrees.OIBTree import OIBTree
from pyramid.threadlocal import get_current_request
from repoze.workflow.workflow import WorkflowError
from zope.component import getAdapter
from zope.component import getUtility

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.unread_aware import UnreadAware
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IVote
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.views.macros import FlashMessages
from voteit.core.validators import html_string_validator
from voteit.core.fields import TZDateTime


_UPCOMING_PERMS = (security.VIEW, security.EDIT, security.DELETE, security.CHANGE_WORKFLOW_STATE, security.MODERATE_MEETING, )

ACL = {}
ACL['private'] = [(Allow, security.ROLE_ADMIN, _UPCOMING_PERMS),
                  (Allow, security.ROLE_MODERATOR, _UPCOMING_PERMS),
                  DENY_ALL,
                   ]
ACL['upcoming'] = [(Allow, security.ROLE_ADMIN, _UPCOMING_PERMS),
                  (Allow, security.ROLE_MODERATOR, _UPCOMING_PERMS),
                  (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                  (Allow, security.ROLE_VOTER, security.VIEW),
                  (Allow, security.ROLE_VIEWER, security.VIEW),
                  DENY_ALL,
                   ]
ACL['ongoing'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.CHANGE_WORKFLOW_STATE, security.MODERATE_MEETING, )),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.CHANGE_WORKFLOW_STATE, security.MODERATE_MEETING, )),
                  (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                  (Allow, security.ROLE_VOTER, (security.VIEW, security.ADD_VOTE, )),
                  (Allow, security.ROLE_VIEWER, security.VIEW),
                  DENY_ALL,
                   ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.CHANGE_WORKFLOW_STATE, )),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW, security.CHANGE_WORKFLOW_STATE, )),
                 (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                 (Allow, security.ROLE_VOTER, security.VIEW),
                 (Allow, security.ROLE_VIEWER, security.VIEW),
                 DENY_ALL,
                ]
CLOSED_STATES = ('canceled', 'closed', )


class Poll(BaseContent, WorkflowAware, UnreadAware):
    """ Poll content. """
    implements(IPoll, ICatalogMetadataEnabled)
    content_type = 'Poll'
    display_name = _(u"Poll")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_POLL

    @property
    def __acl__(self):
        state = self.get_workflow_state()
        if state == u'private':
            return ACL['private']
        if state == u'upcoming':
            return ACL['upcoming']
        if state == u'ongoing':
            return ACL['ongoing']
        return ACL['closed'] #As default - don't traverse to parent

    @property
    def start_time(self):
        return self.get_field_value('start_time')

    @property
    def end_time(self):
        return self.get_field_value('end_time')

    def _get_proposal_uids(self):
        return self.get_field_value('proposals', ())

    def _set_proposal_uids(self, value):
        self.set_field_value('proposals', value)

    proposal_uids = property(_get_proposal_uids, _set_proposal_uids)

    def _get_poll_settings(self):
        return getattr(self, '_poll_settings', {})

    def _set_poll_settings(self, value):
        if not isinstance(value, dict):
            raise TypeError("poll_settings attribute should be a dict")
        self._poll_settings = value

    poll_settings = property(_get_poll_settings, _set_poll_settings)

    def _get_ballots(self):
        return getattr(self, '_ballots', None)

    def _set_ballots(self, value):
        self._ballots = value

    ballots = property(_get_ballots, _set_ballots)

    def _get_poll_result(self):
        return getattr(self, '_poll_result', None)

    def _set_poll_result(self, value):
        self._poll_result = value

    poll_result = property(_get_poll_result, _set_poll_result)

    @property
    def poll_plugin_name(self):
        """ Returns registered poll plugin name. Can be used to get registered utility
        """
        return self.get_field_value('poll_plugin')

    def get_poll_plugin(self):
        return getAdapter(self, name = self.poll_plugin_name, interface = IPollPlugin)

    def get_proposal_objects(self):
        agenda_item = find_interface(self, IAgendaItem)
        if agenda_item is None:
            raise ValueError("Can't find any agenda item in the polls lineage")
        proposals = set()
        for item in agenda_item.values():
            if item.uid in self.proposal_uids:
                proposals.add(item)
        return proposals

    def get_all_votes(self):
        """ Returns all votes in this context. """
        return frozenset([x for x in self.values() if IVote.providedBy(x)])

    def get_voted_userids(self):
        """ Returns userids of all users who've voted. """
        userids = set()
        for vote in self.get_all_votes():
            if not len(vote.creators) == 1:
                raise ValueError("The creators attribute on a vote didn't have a single value. "
                                 "Votes can only have one creator. Vote was: %s" % vote)
            userids.add(vote.creators[0])
        return frozenset(userids)

    def _calculate_ballots(self):
        ballot_counter = Ballots()
        for vote in self.get_all_votes():
            ballot_counter.add(vote.get_vote_data())
        self.ballots = ballot_counter.result()

    def close_poll(self):
        """ Close the poll. """
        request = get_current_request() #Since this is only used once per poll it should be okay
        fm = FlashMessages(request)

        self._calculate_ballots()

        poll_plugin = self.get_poll_plugin()
        poll_plugin.handle_close()

        handle_uids = poll_plugin.change_states_of()

        for (uid, state) in handle_uids.items():
            if uid not in self.proposal_uids:
                raise ValueError("The poll plugins close() method returned a uid that doesn't exist in this poll.")
            proposal = self.get_proposal_by_uid(uid)

            #Adjust state?
            if proposal.get_workflow_state() == state:
                msg = _('change_prop_state_already_that_state_error',
                        default=u"Proposal '${name}' already in state ${state}",
                        mapping={'name':proposal.__name__, 'state':state})
                fm.add(msg)
            else:
                try:
                    proposal.set_workflow_state(request, state)
                    msg = _('prop_state_changed_notice',
                            default=u"Proposal '${name}' set as ${state}",
                            mapping={'name':proposal.__name__, 'state':state})
                    fm.add(msg)
                except WorkflowError:
                    msg = _('prop_state_change_error',
                            default=u"Proposal with id '${name}' couldn't be set as ${state}. You should do this manually.",
                            mapping={'name':proposal.__name__, 'state':state})
                    fm.add(msg, type='error')

        msg = _('poll_closed_info',
                default=u"Poll closed. Proposals might have been adjusted as approved or denied depending on outcome of the poll.")
        fm.add(msg)

    def render_poll_result(self):
        """ Render poll result. Calls plugin to calculate result.
        """
        poll_plugin = self.get_poll_plugin()
        return poll_plugin.render_result()

    def get_proposal_by_uid(self, uid):
        for prop in self.get_proposal_objects():
            if prop.uid == uid:
                return prop
        raise KeyError("No proposal found with UID '%s'" % uid)


class Ballots(object):
    """ Simple object to help counting votes. It's not addable anywhere.
        Should be treatable as an internal object for polls.
    """

    def __init__(self):
        self.ballots = OIBTree()

    def result(self):
        return tuple( sorted( self.ballots.iteritems() ) )

    def add(self, value):
        """ Add a dict of results - a ballot - to the pool. Append and increase counter. """
        if value in self.ballots:
            self.ballots[value] += 1
        else:
            self.ballots[value] = 1


def construct_schema(context=None, request=None, **kwargs):
    if context is None:
        KeyError("'context' is a required keyword for Poll schemas. See construct_schema in the poll module.")
    if request is None:
        KeyError("'request' is a required keyword for Poll schemas. See construct_schema in the poll module.")
    type = kwargs.get('type', None)

    dt_util = getUtility(IDateTimeUtil)

    #Add all selectable plugins to schema. This chooses the poll method to use
    plugin_choices = set()

    #FIXME: The new object should probably be sent to construct schema
    #for now, we can fake this
    fake_poll = Poll()

    for (name, plugin) in request.registry.getAdapters([fake_poll], IPollPlugin):
        plugin_choices.add((name, plugin.title))

    #Proposals to vote on
    proposal_choices = set()
    agenda_item = find_interface(context, IAgendaItem)
    if agenda_item is None:
        Exception("Couldn't find the agenda item from this polls context")
        
    #Get valid proposals - should be in states 'published' to be selectable
    for prop in agenda_item.get_content(iface=IProposal, states='published', sort_on='title'):
        proposal_choices.add((prop.uid, prop.title, ))
        
    # get currently chosen proposals
    if IPoll.providedBy(context):
        for prop in context.get_proposal_objects():
            proposal_choices.add((prop.uid, prop.title, ))
            
    proposal_choices = sorted(proposal_choices, key=lambda proposal: proposal[1].lower())
        
    #Note: The message factory shouldn't process mappings here, it's handled by deform!
    _earliest_start = colander.Range(min=dt_util.localnow(),
                                     min_err=_('${val} is earlier than earliest date ${min}'),)
    _earliest_end = colander.Range(min=dt_util.localnow(),
                                   min_err=_('${val} is earlier than earliest date ${min}'),)

    #base schema
    local_tz = dt_util.timezone


    class PollSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String(),
                                    title = _(u"Title"),
                                    validator=html_string_validator,)
        description = colander.SchemaNode(colander.String(),
                                          title = _(u"Description"),
                                          missing=u"",
                                          description = _(u"Explain your choice of poll method and your plan for the different polls in the agenda item."),
                                          widget=deform.widget.RichTextWidget(),)

        poll_plugin = colander.SchemaNode(colander.String(),
                                          title = _(u"Poll method to use"),
                                          description = _(u"Read in the help wiki about pros and cons of different polling methods."),
                                          #description = _(u"poll_method_description",
                                          #                default=u"Each poll method should contain information about what it does."),
                                          widget=deform.widget.SelectWidget(values=plugin_choices),)
                                          
        proposals = colander.SchemaNode(deform.Set(allow_empty=True), 
                                        name="proposals",
                                        title = _(u"Proposals"),
                                        description = _(u"Only proposals in the state 'published' can be selected"),
                                        #description = _(u"poll_select_proposals_description",
                                        #                default=u"Only proposals in the state 'published' can be selected here."),
                                        missing=set(),
                                        widget=deform.widget.CheckboxChoiceWidget(values=proposal_choices),)

        start_time = colander.SchemaNode(
             TZDateTime(local_tz),
             title = _(u"Start time of this poll."),
             description = _(u"You need to open it yourself."),
             widget=deform.widget.DateTimeInputWidget(options={'timeFormat': 'hh:mm'}),
        )
        end_time = colander.SchemaNode(
             TZDateTime(local_tz),
             title = _(u"End time of this poll."),
             description = _(u"You need to close it yourself."),
             widget=deform.widget.DateTimeInputWidget(options={'timeFormat': 'hh:mm'}),
        )

    return PollSchema()


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, Poll, registry=config.registry)


def closing_poll_callback(content, info):
    """ Workflow callback when a poll is closed. Content is a poll here. """
    content.close_poll()


def upcoming_poll_callback(content, info):
    """ Workflow callback when a poll is set in the upcoming state.
        This method sets all proposals in the locked for vote-state.
    """
    request = get_current_request() #This is an exception - won't be called many times.
    count = 0
    for proposal in content.get_proposal_objects():
        if 'voting' in [x['name'] for x in proposal.get_available_workflow_states(request)]:
            proposal.set_workflow_state(request, 'voting')
            count += 1

    fm = FlashMessages(request)
    msg = _('poll_upcoming_state_notice',
            default=u"Setting poll in upcoming state. It's now visible for meeting participants.")
    fm.add(msg)
    if count:
        #FIXME: Translation mappings
        msg = _(u'poll_closed_proposals_locked_notice',
                default=u"${count} selected proposals were set in the 'locked for vote' state. They can no longer be edited or retracted by normal users.",
                mapping={'count':count})
        fm.add(msg)
        
def ongoing_poll_callback(context, info):
    """ Workflow callback when a poll is set in the ongoing state.
        This method will raise an exeption if the parent agenda item is not ongoing or if there is no propsoals in the poll.
    """
    ai = find_interface(context, IAgendaItem)
    if ai and ai.get_workflow_state() != 'ongoing':
        raise Exception("You can't set a poll to ongoing if the agenda item is not ongoing")

    if not context.proposal_uids:
        raise ValueError('A poll with no proposal can not be set to ongoing')
