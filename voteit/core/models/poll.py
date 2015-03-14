from BTrees.OIBTree import OIBTree
from arche.security import get_acl_registry
from arche.utils import send_email
from pyramid.httpexceptions import HTTPForbidden
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from repoze.workflow.workflow import WorkflowError
from zope.interface import implementer

from voteit.core import _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.date_time_util import utcnow
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IFlashMessages
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IVote
from voteit.core.models.workflow_aware import WorkflowAware


@implementer(IPoll, ICatalogMetadataEnabled)
class Poll(BaseContent, WorkflowAware):
    """ Poll content type.
        See :mod:`voteit.core.models.interfaces.IPoll`.
        All methods are documented in the interface of this class.
        Note that the actual poll method isn't decided by the poll
        content type. It calls a poll plugin to get that.
    """
    type_name = 'Poll'
    type_title = _(u"Poll")
    add_permission = security.ADD_POLL
    _poll_result = None
    _ballots = None
    _poll_settings = None

    @property
    def __acl__(self):
        acl = get_acl_registry()
        #If ai is private, use private
        ai = find_interface(self, IAgendaItem)
        ai_state = ai.get_workflow_state()
        if ai_state == 'private':
            return acl.get_acl('Poll:private')
        state = self.get_workflow_state()
        #As default - don't traverse to parent
        acl_name = 'Poll:%s' % state
        if acl_name in acl:
            return acl.get_acl(acl_name)
        return acl.get_acl('Poll:private')

    @property
    def start_time(self):
        return self.get_field_value('start_time')

    @property
    def end_time(self):
        return self.get_field_value('end_time')

    @property
    def voters_mark_ongoing(self):
        return self.get_field_value('voters_mark_ongoing', frozenset())

    @property
    def voters_mark_closed(self):
        return self.get_field_value('voters_mark_closed', frozenset())

    @property
    def proposals(self):
        return self.get_field_value('proposals', ())
    @proposals.setter
    def proposals(self, value):
        value = tuple(value)
        self.set_field_value('proposals', value)

    proposal_uids = proposals #b/c

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
    def poll_plugin(self):
        return self.get_field_value('poll_plugin')
    @poll_plugin.setter
    def poll_plugin(self, value):
        self.set_field_value('poll_plugin', value)

    poll_plugin_name = poll_plugin #b/c

    def get_poll_plugin(self):
        reg = get_current_registry()
        return reg.getAdapter(self, name = self.poll_plugin_name, interface = IPollPlugin)

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
            userids.add(vote.__name__)
        return frozenset(userids)

    def _calculate_ballots(self):
        ballot_counter = Ballots()
        for vote in self.get_all_votes():
            ballot_counter.add(vote.get_vote_data())
        self.ballots = ballot_counter.result()

    def close_poll(self):
        """ Close the poll. """
        self._calculate_ballots()
        poll_plugin = self.get_poll_plugin()
        poll_plugin.handle_close()
        uid_states = poll_plugin.change_states_of()
        if uid_states:
            self.adjust_proposal_states(uid_states)
        self.set_field_appstruct({'end_time': utcnow()})

    def adjust_proposal_states(self, uid_states, request = None):
        assert isinstance(uid_states, dict)
        if request is None:
            request = get_current_request()
        locale = request.localizer
        fm = IFlashMessages(request)

        for (uid, state) in uid_states.items():
            if uid not in self.proposal_uids:
                raise ValueError("The poll plugins close() method returned a uid that doesn't exist in this poll.")
            proposal = self.get_proposal_by_uid(uid)
            #Adjust state?
            prop_wf_state = proposal.get_workflow_state()
            #Message strings can't contain other message strings, so we'll translate the state first
            translated_state = locale.translate(_(state.title()))
            if prop_wf_state == state:
                msg = _('change_prop_state_already_that_state_error',
                        default=u"Proposal '${name}' already in state ${state}",
                        mapping={'name':proposal.__name__, 'state':translated_state})
                fm.add(msg)
            else:
                try:
                    proposal.set_workflow_state(request, state)
                    msg = _('prop_state_changed_notice',
                            default=u"Proposal '${name}' set as ${state}",
                            mapping={'name':proposal.__name__, 'state':translated_state})
                    fm.add(msg)
                except WorkflowError:
                    msg = _('prop_state_change_error',
                            default=u"Proposal with id '${name}' couldn't be set as ${state}. You should do this manually.",
                            mapping={'name':proposal.__name__, 'state':translated_state})
                    fm.add(msg, type='error')

        msg = _('poll_closed_info',
                default=u"Poll closed. Proposals might have been adjusted as approved or denied depending on outcome of the poll.")
        fm.add(msg)

    def render_poll_result(self, request, api, complete=True):
        """ Render poll result. Calls plugin to calculate result.
            FIXME: Remove this
        """
        try:
            poll_plugin = self.get_poll_plugin()
            return poll_plugin.render_result(request, api, complete)
        except Exception, exc: # pragma : no cover
            if request.registry.settings.get('pyramid.debug_templates', False):
                raise exc
            return _(u"broken_plugin_error",
                     default = u"Broken poll plugin. Can't display result. Turn on debug_templates to see the error.")

    def get_proposal_by_uid(self, uid):
        for prop in self.get_proposal_objects():
            if prop.uid == uid:
                return prop
        raise KeyError("No proposal found with UID '%s'" % uid)


class Ballots(object):
    """ Simple object to help counting votes. It's not addable anywhere.
        Should be treated as an internal object for polls.
    """

    def __init__(self):
        """ Ballots attr is an OIBTree, since they can have any object as key.
        """
        self.ballots = OIBTree()

    def result(self):
        """ Return a tuple with sorted ballot items. """
        return tuple( sorted( self.ballots.iteritems() ) )

    def add(self, value):
        """ Add a dict of results - a ballot - to the pool. Append and increase counter. """
        if value in self.ballots:
            self.ballots[value] += 1
        else:
            self.ballots[value] = 1


def closing_poll_callback(poll, info):
    """ Workflow callback when a poll is closed."""
    poll.close_poll()

def lock_proposals(poll, request):
    """ Set proposals to voting. """
    count = 0
    for proposal in poll.get_proposal_objects():
        if 'voting' in [x['name'] for x in proposal.get_available_workflow_states(request)]:
            proposal.set_workflow_state(request, 'voting')
            count += 1
    if count:
        fm = IFlashMessages(request, None)
        if fm:
            singular = request.localizer.translate(_(u"proposal"))
            plural = request.localizer.translate(_(u"proposals"))
            prop_form = request.localizer.pluralize(singular, plural, count)
            msg = _(u'poll_proposals_locked_notice',
                    default=u"Setting ${count} ${prop_form} as 'locked for vote'. "
                            u"They can no longer be edited or retracted by normal users. "
                            u"All proposals participating in an ongoing poll should be locked.",
                    mapping={'count':count,
                             'prop_form': prop_form})
            fm.add(msg)

def upcoming_poll_callback(poll, info):
    """ Workflow callback when a poll is set in the upcoming state.
        This method sets all proposals in the locked for vote-state.
    """
    request = get_current_request()
    lock_proposals(poll, request)
    fm = IFlashMessages(request, None)
    if fm:
        msg = _('poll_upcoming_state_notice',
                default=u"Setting poll in upcoming state. It's now visible for meeting participants.")
        fm.add(msg)

def ongoing_poll_callback(poll, info):
    """ Workflow callback when a poll is set in the ongoing state.
        This method will raise an exeption if the parent agenda item is not ongoing or if there is no proposals in the poll.
    """
    ai = find_interface(poll, IAgendaItem)
    if ai.get_workflow_state() != 'ongoing':
        err_msg = _(u"error_poll_cant_be_ongoing_unless_ai_is",
                    default = u"You can't set a poll to ongoing if the agenda item is not ongoing.")
        raise HTTPForbidden(err_msg)
    request = get_current_request()
    if not poll.proposal_uids:
        edit_tag = '<a href="%s"><b>%s</b></a>' % (request.resource_url(poll, 'edit'), poll.title)
        err_msg = _(u"error_no_proposals_in_poll",
                    default = u"A poll with no proposal can not be set to ongoing. Click link to edit: ${tag}",
                    mapping = {'tag': edit_tag})
        raise HTTPForbidden(err_msg)
    lock_proposals(poll, request)

def email_voters_about_ongoing_poll(poll, request=None):
    """ Email voters about that a poll they have voting permission in is open.
        I.e. in state ongoing.
        This function is triggered by a workflow subscriber, so not all functionality
        is nested in the workflow callback. (It would make permission tests very
        annoying and hard to write otherwise)

        Note that there's a setting on the meeting called poll_notification_setting
        that controls wether this should be executed or not.
    """
    meeting = find_interface(poll, IMeeting)
    assert meeting
    if not meeting.get_field_value('poll_notification_setting', True):
        return
    if request is None:
        request = get_current_request()
    userids = security.find_authorized_userids(poll, (security.ADD_VOTE,))
    root = find_root(meeting)
    users = root['users']
    email_addresses = set()
    for userid in userids:
        #In case user is deleted, they won't have the required permission either
        #find_authorized_userids loops through the users folder
        email = users[userid].email
        if email:
            email_addresses.add(email)
    response = {}
    response['meeting'] = meeting
    response['meeting_url'] = request.resource_url(meeting)
    response['poll_url'] = request.resource_url(poll)
    sender = "%s <%s>" % (meeting.get_field_value('meeting_mail_name'), meeting.get_field_value('meeting_mail_address'))
    #FIXME: This should be detatched into a view component
    body_html = render('../views/templates/email/ongoing_poll_notification.pt', response, request=request)
    #Since subject won't be part of a renderer, we need to translate it manually
    #Keep the _ -syntax otherwise Babel/lingua won't pick up the string
    subject = _(u"VoteIT: Open poll")
    for email in email_addresses:
        send_email(request, subject, [email], body_html)


def includeme(config):
    config.add_content_factory(Poll, addable_to = 'AgendaItem')
    aclreg = config.registry.acl

    _UPCOMING_PERMS = (security.VIEW,
                       security.EDIT,
                       security.DELETE,
                       security.CHANGE_WORKFLOW_STATE,
                       security.MODERATE_MEETING, )
    _ONGOING_PERMS = (security.VIEW,
                      security.DELETE,
                      security.CHANGE_WORKFLOW_STATE,
                      security.MODERATE_MEETING, )

    private = aclreg.new_acl('Poll:private')
    private.add(security.ROLE_ADMIN, _UPCOMING_PERMS)
    private.add(security.ROLE_MODERATOR, _UPCOMING_PERMS)
    upcoming = aclreg.new_acl('Poll:upcoming')
    upcoming.add(security.ROLE_ADMIN, _UPCOMING_PERMS)
    upcoming.add(security.ROLE_MODERATOR, _UPCOMING_PERMS)
    upcoming.add(security.ROLE_VIEWER, security.VIEW)
    ongoing = aclreg.new_acl('Poll:ongoing')
    ongoing.add(security.ROLE_ADMIN, _ONGOING_PERMS)
    ongoing.add(security.ROLE_MODERATOR, _ONGOING_PERMS)
    ongoing.add(security.ROLE_VOTER, security.ADD_VOTE)
    ongoing.add(security.ROLE_VIEWER, security.VIEW)
    closed = aclreg.new_acl('Poll:closed')
    closed.add(security.ROLE_ADMIN, [security.VIEW, security.DELETE, security.MODERATE_MEETING])
    closed.add(security.ROLE_MODERATOR, [security.VIEW, security.DELETE, security.MODERATE_MEETING])
    closed.add(security.ROLE_VIEWER, security.VIEW)
    canceled = aclreg.new_acl('Poll:canceled')
    canceled.add(security.ROLE_ADMIN, _ONGOING_PERMS)
    canceled.add(security.ROLE_MODERATOR, _ONGOING_PERMS)
    canceled.add(security.ROLE_VIEWER, security.VIEW)
