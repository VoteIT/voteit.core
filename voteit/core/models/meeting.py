from BTrees.OOBTree import OOBTree
from arche.interfaces import IObjectAddedEvent
from arche.interfaces import IWorkflowBeforeTransition
from arche.portlets import get_portlet_manager
from arche.resources import ContextACLMixin
from pyramid.httpexceptions import HTTPForbidden
from pyramid.traversal import find_root
from repoze.catalog.query import Eq
from repoze.folder import unicodify
from zope.interface import implementer

from voteit.core import _
from voteit.core import security
from voteit.core.models.arche_compat import createContent
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.poll import PROPOSAL_ORDER_CHOICES
from voteit.core.models.poll import PROPOSAL_ORDER_DEFAULT
from voteit.core.models.workflow_aware import WorkflowCompatMixin
from voteit.core.models.security_aware import SecurityAware


@implementer(IMeeting)
class Meeting(BaseContent, SecurityAware, ContextACLMixin, WorkflowCompatMixin):
    """ Meeting content type.
        See :mod:`voteit.core.models.interfaces.IMeeting`.
        All methods are documented in the interface of this class.
    """
    type_name = 'Meeting'
    type_title = _("Meeting")
    nav_visible = False
    add_permission = security.ADD_MEETING
    hide_meeting = False #Unless it's been set, don't show meeting
    nav_title = ""
    custom_mutators = {'copy_perms_and_users': 'copy_perms_and_users'}
    proposal_id_method = ""
    # To set that this should keep track of ordering. See repoze.folder
    # If _order is set to None, ordering isn't stored
    _order = ()

    def __init__(self, data=None, **kwargs):
        """ When meetings are added, whoever added them should become moderator and voter.
            BaseContent will have added userid to creators attribute.
        """
        if 'access_policy' not in kwargs:
            kwargs['access_policy'] = 'invite_only'
        super(Meeting, self).__init__(data=data, **kwargs)
        if len(self.creators) and self.creators[0]:
            userid = self.creators[0]
            #We can't send the event here since the object isn't attached to the resource tree yet
            #When it is attached, an event will be sent.
            self.add_groups(userid, (security.ROLE_MODERATOR, ), event = False)

    @property
    def order(self):
        if self._order is not None:
            return list(self._order)
        return self.data.keys()
    @order.setter
    def order(self, value):
        pool = list(self.data.keys())
        new_order = []
        for key in value:
            new_order.append(key)
            pool.remove(key)
        if pool:
            new_order.extend(pool)
        self._order = tuple([unicodify(x) for x in new_order])

    @property
    def body(self): #arche compat
        return self.get_field_value('body', '')
    @body.setter
    def body(self, value):
        self.set_field_value('body', value)

    @property
    def start_time(self):
        return self.get_field_value('start_time')
    @start_time.setter
    def start_time(self, value):
        return self.set_field_value('start_time', value)

    @property
    def end_time(self):
        return self.get_field_value('end_time')
    @end_time.setter
    def end_time(self, value):
        return self.set_field_value('end_time', value)

    @property
    def meeting_mail_name(self): #arche compat
        return self.get_field_value('meeting_mail_name')
    @meeting_mail_name.setter
    def meeting_mail_name(self, value):
        self.set_field_value('meeting_mail_name', value)

    @property
    def meeting_mail_address(self): #arche compat
        return self.get_field_value('meeting_mail_address')
    @meeting_mail_address.setter
    def meeting_mail_address(self, value):
        self.set_field_value('meeting_mail_address', value)

    @property
    def public_description(self): #arche compat
        return self.get_field_value('public_description')
    @public_description.setter
    def public_description(self, value):
        self.set_field_value('public_description', value)

    @property
    def poll_notification_setting(self): #arche compat
        return self.get_field_value('poll_notification_setting', False)
    @poll_notification_setting.setter
    def poll_notification_setting(self, value):
        self.set_field_value('poll_notification_setting', value)

    @property
    def mention_notification_setting(self): #arche compat
        return self.get_field_value('mention_notification_setting', True)
    @mention_notification_setting.setter
    def mention_notification_setting(self, value):
        self.set_field_value('mention_notification_setting', value)

    @property
    def access_policy(self): #arche compat
        return self.get_field_value('access_policy')
    @access_policy.setter
    def access_policy(self, value):
        self.set_field_value('access_policy', value)

    @property
    def hide_proposal_states(self): #arche compat
        return self.get_field_value('hide_proposal_states', ('retracted', 'denied', 'unhandled'))
    @hide_proposal_states.setter
    def hide_proposal_states(self, value):
        self.set_field_value('hide_proposal_states', value)

    @property
    def system_userids(self):
        return self.get_field_value('system_userids', ())
    @system_userids.setter
    def system_userids(self, value):
        self.set_field_value('system_userids', tuple(value))

    @property
    def polls_menu_only_links(self):  # Arche compat
        return self.get_field_value('polls_menu_only_links')
    @polls_menu_only_links.setter
    def polls_menu_only_links(self, value):
        self.set_field_value('polls_menu_only_links', value)

    @property
    def poll_proposals_default_order(self):
        return self.get_field_value('poll_proposals_default_order', PROPOSAL_ORDER_DEFAULT)
    @poll_proposals_default_order.setter
    def poll_proposals_default_order(self, value):
        order_dict = dict(PROPOSAL_ORDER_CHOICES)
        assert value in order_dict, 'Default order must be one of: {}'.format(', '.join(order_dict.keys()))
        self.set_field_value('poll_proposals_default_order', value)

    @property
    def tags(self):
        return self.get_field_value('tags', frozenset())
    @tags.setter
    def tags(self, value):
        return self.set_field_value('tags', frozenset(value))

    @property
    def invite_tickets(self):
        try:
            return self.__invite_tickets__
        except AttributeError:
            self.__invite_tickets__ = OOBTree()
            return self.__invite_tickets__

    def get_ticket_names(self, previous_invites = 0):
        assert isinstance(previous_invites, int)
        results = []
        for (name, ticket) in self.invite_tickets.items():
            if previous_invites < 0:
                continue
            if previous_invites >= len(ticket.sent_dates):
                results.append(name)
        return results

    def add_invite_ticket(self, email, roles, sent_by = None):
        if email in self.invite_tickets:
            return
        obj = createContent('InviteTicket', email, roles, sent_by = sent_by)
        obj.__parent__ = self
        self.invite_tickets[email] = obj
        return obj

    @property
    def diff_text_enabled(self):
        return self.get_field_value('diff_text_enabled', None)
    @diff_text_enabled.setter
    def diff_text_enabled(self, value):
        self.set_field_value('diff_text_enabled', bool(value))


def add_default_portlets_meeting(meeting):
    manager = get_portlet_manager(meeting)
    if manager is not None:
        if not manager.get_portlets('agenda_item', 'ai_polls'):
            manager.add('agenda_item', 'ai_polls')
        if not manager.get_portlets('agenda_item', 'ai_proposals'):
            ai_proposals = manager.add('agenda_item', 'ai_proposals')
            ai_proposals.settings = {'hide_proposal_states': ('retracted', 'denied', 'unhandled')}
        if not manager.get_portlets('agenda_item', 'ai_discussions'):
            manager.add('agenda_item', 'ai_discussions')
        if not manager.get_portlets('left_fixed', 'agenda_fixed'):
            manager.add('left_fixed', 'agenda_fixed')


def _add_portlets_meeting_subscriber(meeting, event):
    add_default_portlets_meeting(meeting)


def check_no_open_ais(meeting, event):
    """ Make sure no agenda items are ongoing if we close the meeting. """
    if event.to_state == 'closed':
        root = find_root(meeting)
        query = Eq('type_name', 'AgendaItem') & Eq('wf_state', 'ongoing')
        res = root.catalog.query(query)[0]
        if res.total:
            err_msg = _(u"error_cant_close_meeting_with_ongoing_ais",
                        default = u"This meeting still has ongoing or upcoming "
                        "Agenda items in it. You can't close it until they're closed.")
            raise HTTPForbidden(err_msg)


def includeme(config):
    config.add_content_factory(Meeting, addable_to = 'Root')
    config.add_subscriber(_add_portlets_meeting_subscriber, [IMeeting, IObjectAddedEvent])
    config.add_subscriber(check_no_open_ais, [IMeeting, IWorkflowBeforeTransition])
