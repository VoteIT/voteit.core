from datetime import datetime

import colander
import deform
from zope.interface import implements
from pyramid.traversal import find_interface, find_root
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS
from BTrees.OOBTree import OOBTree
from pyramid.threadlocal import get_current_request
from repoze.workflow.workflow import WorkflowError
from zope.component import getAdapter

from voteit.core import security
from voteit.core import register_content_info
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IVote
from voteit.core.views.macros import FlashMessages


ACL = {}
ACL['private'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, security.DELETE, )),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.DELETE, )),
                  DENY_ALL,
                   ]
ACL['planned'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, security.DELETE, )),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.DELETE, )),
                  (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                  (Allow, security.ROLE_VOTER, security.VIEW),
                  (Allow, security.ROLE_VIEWER, security.VIEW),
                  DENY_ALL,
                   ]
ACL['ongoing'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, )),
                  (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, )),
                  (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                  (Allow, security.ROLE_VOTER, (security.VIEW, security.ADD_VOTE, )),
                  (Allow, security.ROLE_VIEWER, security.VIEW),
                  DENY_ALL,
                   ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, security.VIEW),
                 (Allow, security.ROLE_MODERATOR, security.VIEW),
                 (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                 (Allow, security.ROLE_VOTER, security.VIEW),
                 (Allow, security.ROLE_VIEWER, security.VIEW),
                 DENY_ALL,
                ]
CLOSED_STATES = ('canceled', 'closed', )


class Poll(BaseContent, WorkflowAware):
    """ Poll content. """
    implements(IPoll)
    content_type = 'Poll'
    display_name = _(u"Poll")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_POLL

    @property
    def __acl__(self):
        state = self.get_workflow_state()
        if state == u'private':
            return ACL['private']
        if state == u'planned':
            return ACL['planned']
        if state == u'ongoing':
            return ACL['ongoing']
        return ACL['closed'] #As default - don't traverse to parent
    
    #proposals
    def _get_proposal_uids(self):
        return self.get_field_value('proposals', ())

    def _set_proposal_uids(self, value):
        self.set_field_value('proposals', value)

    proposal_uids = property(_get_proposal_uids, _set_proposal_uids)

    def set_raw_poll_data(self, value):
        self._raw_poll_data = value
    
    def get_raw_poll_data(self):
        return getattr(self, '_raw_poll_data', None)

    def set_poll_result(self, value):
        self._poll_result = value
    
    def get_poll_result(self):
        return getattr(self, '_poll_result', None)

    @property
    def poll_plugin_name(self):
        """ Returns registered poll plugin name. Can be used to get registered utility
        """
        return self.get_field_value('poll_plugin')

    def get_poll_plugin(self):
        return getAdapter(self, name = self.poll_plugin_name, interface = IPollPlugin)

    def get_proposal_objects(self):
        agenda_item = find_interface(self, IAgendaItem)
        proposals = set()
        if agenda_item is None:
            return proposals
        for item in agenda_item.values():
            if item.uid in self.proposal_uids:
                proposals.add(item)
        return proposals

    def get_all_votes(self):
        """ Returns all votes in this context. """
        return frozenset([x for x in self.values() if IVote.providedBy(x)])

    def get_voted_userids(self):
        """ Returns userids of all users who've voted. """
        userids = [x.creators[0] for x in self.get_all_votes()]
        return frozenset(userids)
    
    def get_ballots(self):
        """ Returns unique ballots and their counts. In the format:
            [{'ballot':x,'count':y}, <etc...>]
            The x in ballot can be any type of object. It's just what
            this polls plugin considers to be a vote.
        """
        ballot_counter = Ballots()
        for vote in self.get_all_votes():
            ballot_counter.add(vote.get_vote_data())
        return ballot_counter.get_result()

    def close_poll(self):
        """ Close the poll. """
        request = get_current_request() #Since this is only used once per poll it should be okay
        fm = FlashMessages(request)
        
        ballots = self.get_ballots()
        self.set_raw_poll_data(ballots)
        
        poll_plugin = self.get_poll_plugin()
        
        self.set_poll_result(poll_plugin.get_result(ballots))
        handle_uids = poll_plugin.change_states_of()

        for (uid, state) in handle_uids.items():
            if uid not in self.proposal_uids:
                raise ValueError("The poll plugins close() method returned a uid that doesn't exist in this poll.")
            proposal = self.get_proposal_by_uid(uid)
            
            #Adjust state?
            if proposal.get_workflow_state() == state:
                msg = _(u"Proposal '%s' already in state %s" % (proposal.__name__, state))
                fm.add(msg)
            else:
                try:
                    proposal.set_workflow_state(request, state)
                    msg = _(u"Proposal '%s' set as %s" % (proposal.__name__, state))
                    fm.add(msg)
                except WorkflowError:
                    msg = _(u"Proposal with id '%s' couldn't be set as %s. You should do this manually." % (proposal.__name__, state))
                    fm.add(msg, type='error')
        
        msg = _(u"Poll closed. Proposals might have been adjusted as approved or denied depending on outcome of the poll.")
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
        self.ballots = OOBTree()

    def get_result(self):
        """ Return data formated as a dictionary. """
        return [{'ballot':x,'count':y} for x, y in self.ballots.items()]
    
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


    #Add all selectable plugins to schema. This chooses the poll method to use
    plugin_choices = set()

    #FIXME: The new object should probably be sent to construct schema
    #for now, we can fake this
    poll = Poll()

    for (name, plugin) in request.registry.getAdapters([poll], IPollPlugin):
        plugin_choices.add((name, plugin.title))

    #Proposals to vote on
    proposal_choices = set()
    agenda_item = find_interface(context, IAgendaItem)
    if agenda_item is None:
        Exception("Couldn't find the agenda item from this polls context")
    [proposal_choices.add((x.uid, x.title)) for x in agenda_item.values() if x.content_type == 'Proposal']
    
    _earliest_start = colander.Range(min=datetime.now(),
                                     min_err=_('${val} is earlier than earliest date ${min}'),)
    _earliest_end = colander.Range(min=datetime.now(),
                                   min_err=_('${val} is earlier than earliest date ${min}'),)

    #base schema
    class PollSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(colander.String())
        #FIXME: Add later
#        start = colander.SchemaNode(colander.DateTime(),
#                                    title = _(u"Start time"),
#                                    default = datetime.now(),
#                                    validator=_earliest_start,
#                                    )
#        end = colander.SchemaNode(colander.DateTime(),
#                                    title = _(u"End time"),
#                                    default = datetime.now(),
#                                    validator=_earliest_end,
#                                    )
        
        poll_plugin = colander.SchemaNode(colander.String(),
                                          widget=deform.widget.SelectWidget(values=plugin_choices),)
        proposals = colander.SchemaNode(deform.Set(),
                                        name="proposals",
                                        widget=deform.widget.CheckboxChoiceWidget(values=proposal_choices),)

    return PollSchema()


def includeme(config):
    register_content_info(construct_schema, Poll, registry=config.registry)

    
def closing_poll_callback(content, info):
    """ Workflow callback when a poll is closed. Content is a poll here. """
    content.close_poll()

def planned_poll_callback(content, info):
    """ Workflow callback when a poll is set in the planned state.
        This method sets all proposals in the locked for vote-state.
    """
    request = get_current_request() #This is an exception - won't be called many times.
    count = 0
    for proposal in content.get_proposal_objects():
        if 'voting' in [x['name'] for x in proposal.get_available_workflow_states(request)]:
            proposal.set_workflow_state(request, 'voting')
            count += 1
    
    fm = FlashMessages(request)
    msg = _(u"Setting poll in planned state. It's now visible for meeting participants.")
    fm.add(msg)
    if count:
        #FIXME: Translation mappings
        msg = _(u"%s selected proposals were set in the 'locked for vote' state. They can no longer be edited or retracted by normal users." % count)
        fm.add(msg)
