from zope.interface import implements
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from BTrees.OIBTree import OIBTree
from pyramid.threadlocal import get_current_request
from repoze.workflow.workflow import WorkflowError
from zope.component import getAdapter
from pyramid.url import resource_url
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.renderers import render
from betahaus.pyracont.decorators import content_factory

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.unread_aware import UnreadAware
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IVote
from voteit.core.views.macros import FlashMessages


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


@content_factory('Poll', title=_(u"Poll"))
class Poll(BaseContent, WorkflowAware, UnreadAware):
    """ Poll content. """
    implements(IPoll, ICatalogMetadataEnabled)
    content_type = 'Poll'
    display_name = _(u"Poll")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_POLL
    schemas = {'add': 'PollSchema', 'edit': 'PollSchema'}

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


def email_voters_about_ongoing_poll(poll, request=None):
    """ Email voters about that a poll they have voting permission in is open.
        I.e. in state ongoing.
        This function is triggered by a workflow subscriber, so not all functionality
        is nested in the workflow callback. (It would make permission tests very
        annoying and hard to write otherwise)
    """
    if request is None:
        request = get_current_request()
    userids = security.find_authorized_userids(poll, (security.ADD_VOTE,))

    meeting = find_interface(poll, IMeeting)
    assert meeting

    root = find_root(meeting)
    users = root['users']
    email_addresses = set()
    for userid in userids:
        user = users.get(userid)
        #In case user is deleted
        if not user:
            continue
        email = user.get_field_value('email')
        if email:
            email_addresses.add(email)

    response = {}
    response['meeting'] = meeting
    response['meeting_url'] = resource_url(meeting, request)
    response['poll_url'] = resource_url(poll, request)

    sender = "%s <%s>" % (meeting.get_field_value('meeting_mail_name'), meeting.get_field_value('meeting_mail_address'))
    body_html = render('../views/templates/email/ongoing_poll_notification.pt', response, request=request)

    mailer = get_mailer(request)
    #We need to send individual messages anyway
    for email in email_addresses:
        msg = Message(subject=_(u"VoteIT: Open poll"),
                      sender = sender,
                      recipients=[email,],
                      html=body_html)
        mailer.send(msg)
