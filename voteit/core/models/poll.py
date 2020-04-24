from __future__ import unicode_literals

from random import random

from BTrees.OIBTree import OIBTree
from BTrees.OOBTree import OOBTree
from arche.security import get_acl_registry
from arche.utils import get_flash_messages
from arche.utils import send_email
from arche.utils import utcnow
from pyramid.httpexceptions import HTTPForbidden
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from pyramid.traversal import find_resource
from pyramid.traversal import find_root
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from repoze.workflow.workflow import WorkflowError
from voteit.core.exceptions import BadPollMethodError
from zope.interface import implementer

from voteit.core import _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IFlashMessages
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IVote
from voteit.core.models.workflow_aware import WorkflowAware

# FIXME: This should turn into utilities later on, so other packages can
# register methods without patching.
PROPOSAL_ORDER_ALPHABETICAL = 'alphabatical'
PROPOSAL_ORDER_RANDOM = 'random'
PROPOSAL_ORDER_CHRONOLOGICAL = 'chronological'
PROPOSAL_ORDER_DEFAULT = PROPOSAL_ORDER_CHRONOLOGICAL

PROPOSAL_ORDER_CHOICES = (
    (PROPOSAL_ORDER_CHRONOLOGICAL, _('Chronological')),
    (PROPOSAL_ORDER_ALPHABETICAL, _('Alphabetical')),
    (PROPOSAL_ORDER_RANDOM, _('Random')),
)
PROPOSAL_ORDER_KEY_METHODS = {
    PROPOSAL_ORDER_ALPHABETICAL: lambda p: p.text.lower(),
    PROPOSAL_ORDER_RANDOM: lambda p: random(),
    PROPOSAL_ORDER_CHRONOLOGICAL: lambda p: p.created,
}


@implementer(IPoll)
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
    css_icon = 'glyphicon glyphicon-star'

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

    def add(self, name, other, send_events=True):
        assert IVote.providedBy(other)
        super(Poll, self).add(name, other, send_events=send_events)

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

    @property
    def poll_settings(self):
        try:
            return self._poll_settings
        except AttributeError:
            self._poll_settings = OOBTree()
            return self._poll_settings
    @poll_settings.setter
    def poll_settings(self, value):
        self._poll_settings = OOBTree(value)

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
        return reg.getAdapter(self, name = self.poll_plugin, interface = IPollPlugin)

    @property
    def proposal_order(self):
        return self.get_field_value('proposal_order', '')
    @proposal_order.setter
    def proposal_order(self, value):
        self.set_field_value('proposal_order', value)

    def get_proposal_objects(self):
        """ Return proposal objects relevant to this poll.
            Will sort them in specified order.
        """
        agenda_item = self.__parent__
        if agenda_item is None:
            raise ValueError("Can't find any agenda item in the polls lineage")
        query = Any('uid', tuple(self.proposal_uids)) & Eq('type_name', 'Proposal')
        root = find_root(agenda_item)
        results = []
        for docid in root.catalog.query(query)[1]:
            path = root.document_map.address_for_docid(docid)
            obj = find_resource(root, path)
            # Permission check shouldn't be needed at this point
            if obj:
                results.append(obj)
        if self.proposal_order:
            proposal_order = self.proposal_order
        else:
            meeting = find_interface(self, IMeeting)
            # During tests, we might not have a real meeting here :)
            proposal_order = getattr(meeting, 'poll_proposals_default_order', '')
        key_method = PROPOSAL_ORDER_KEY_METHODS.get(
            proposal_order, PROPOSAL_ORDER_KEY_METHODS[PROPOSAL_ORDER_DEFAULT]
        )
        return sorted(results, key=key_method)

    def calculate_ballots(self):
        ballot_counter = Ballots()
        for vote in self.values():
            assert IVote.providedBy(vote)
            ballot_counter.add(vote.get_vote_data())
        return ballot_counter.result()

    def close_poll(self):
        """ Close the poll. """
        self.ballots = self.calculate_ballots()
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
        changed = []
        change_error = []
        for (uid, state) in uid_states.items():
            if uid not in self.proposal_uids:
                raise ValueError("The poll plugins close() method returned a uid that doesn't exist in this poll.")
            proposal = self.get_proposal_by_uid(uid)
            #Adjust state?
            prop_wf_state = proposal.get_workflow_state()
            if prop_wf_state != state:
                try:
                    proposal.set_workflow_state(request, state)
                    changed.append(proposal)
                except WorkflowError:
                    change_error.append(proposal)
        fm = get_flash_messages(request)
        msg = _('poll_closed_info',
                default = "Poll has now closed. ${num} proposal(s) are now set in another state due to the outcome of the poll.",
                mapping = {'num': len(changed)})
        fm.add(msg)
        if change_error:
            msg = _('poll_closed_proposal_wf_change_error',
                    default = "Couldn't adjust the state of the following proposal(s): '${props}'. "
                    "You may wish to review them manually.",
                    mapping = {'props': "', '".join(prop.aid for prop in change_error)})
            fm.add(msg, type = 'danger')

    def get_proposal_by_uid(self, uid):
        #FIXME: This should be removed. request.resolve_uid instead
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
        try:
            proposal.set_workflow_state(request, 'voting')
            count += 1
        except WorkflowError:
            # Skip those
            pass
    if count:
        fm = IFlashMessages(request, None)
        if fm:
            singular = request.localizer.translate(_(u"proposal"))
            plural = request.localizer.translate(_(u"proposals"))
            prop_form = request.localizer.pluralize(singular, plural, count)
            msg = _(u'poll_proposals_locked_notice',
                    default=u"Setting ${count} ${prop_form} as 'locked for vote'. "
                            u"They can no longer be edited or retracted by normal users. ",
                    mapping={'count':count,
                             'prop_form': prop_form})
            fm.add(msg)


def upcoming_poll_callback(poll, info):
    """ Workflow callback when a poll is set in the upcoming state.
        This method sets all proposals in the locked for vote-state.
    """
    request = get_current_request()
    lock_proposals(poll, request)


def ongoing_poll_callback(poll, info):
    """ Workflow callback when a poll is set in the ongoing state.
        This method will raise an exception if the parent agenda item is not ongoing or if there is no proposals in the poll.
    """
    ai = find_interface(poll, IAgendaItem)
    if ai.get_workflow_state() != 'ongoing':
        err_msg = _(u"error_poll_cant_be_ongoing_unless_ai_is",
                    default = u"You can't set a poll to ongoing if the agenda item is not ongoing.")
        raise HTTPForbidden(err_msg)
    request = get_current_request()
    if not poll.proposal_uids:
        edit_tag = '<a href="%s"><b>%s</b></a>' % (request.resource_url(poll, 'edit_proposals'), poll.title)
        err_msg = _(u"error_no_proposals_in_poll",
                    default = u"A poll with no proposal can not be set to ongoing. Click link to edit: ${tag}",
                    mapping = {'tag': edit_tag})
        raise HTTPForbidden(err_msg)
    poll_plugin = poll.get_poll_plugin()
    try:
        poll_plugin.handle_start(request)
    except BadPollMethodError as exc:
        # Moderators may manually override
        if not exc.override_confirmed:
            raise exc
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
    if not meeting.get_field_value('poll_notification_setting', False):
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
    body_html = render('voteit.core:templates/email/ongoing_poll_notification.pt', response, request=request)
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
