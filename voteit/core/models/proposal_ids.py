from BTrees.OOBTree import OOBTree
from zope.interface import implementer
from zope.component import adapter
from pyramid.threadlocal import get_current_registry
from pyramid.traversal import find_interface
from repoze.folder.interfaces import IObjectAddedEvent

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IProposalIds
from voteit.core import _


@adapter(IMeeting)
@implementer(IProposalIds)
class ProposalIds(object):
    """ Proposal id adapter.
        See :mod:`voteit.core.models.interfaces.IProposalIds`.
        All methods are documented in the interface of this class.
    """
    title = ""
    name = ""

    def __init__(self, context):
        self.context = context

    @property
    def proposal_ids(self):
        try:
            return self.context.__proposal_ids__
        except AttributeError:
            self.context.__proposal_ids__ = OOBTree()
            return self.context.__proposal_ids__

    def add(self, proposal): #pragma : no coverage
        raise NotImplementedError()


class UserIDBasedPropsalIds(ProposalIds):
    """ Add proposal ids based on UserID. IDs are never reused and counts upwards
        with the structure userid-number, Ie john_doe-1 for the first proposal.
    """
    title = _("UserID-based (default)")
    name = ""

    def add(self, proposal):
        if not proposal.creator:
            raise ValueError("The object %s doesn't have a creator assigned. Can't generate automatic id." % proposal)
        #By convention, first name in list is main creator.
        #No support for many creators yet but it might be implemented.
        creator = proposal.creator[0]
        if proposal.aid:
            try:
                if proposal.aid_int > int(self.proposal_ids.get(creator, 0)):
                    self.proposal_ids[creator] = proposal.aid_int
            except (KeyError, TypeError, ValueError): #pragma: no cover
                pass
        else:
            aid_int = self.proposal_ids.get(creator, 0) + 1
            aid = "%s-%s" % (creator, aid_int)
            proposal.set_field_appstruct({'aid': aid, 'aid_int': aid_int})
            self.proposal_ids[creator] = aid_int


class AgendaItemBasedProposalIds(ProposalIds):
    """ Count agenda items instead of userids. """
    title = _("Agenda hashtag")
    name = "ai_hashtag"

    def add(self, proposal):
        ai = find_interface(proposal, IAgendaItem)
        tag_name = ai.hashtag
        if not tag_name:
            tag_name = ai.__name__
        if proposal.aid:
            try:
                # Find the name part and increase the number for it
                # In case this crashes, some props might get the same id
                # This will still be the case since we don't know what's copied,
                # so we'll leave that for the moderators to fix if they want to.
                curr_name = "-".join(proposal.aid.split('-')[:-1])
                if proposal.aid_int > int(self.proposal_ids.get(curr_name, 0)):
                    self.proposal_ids[curr_name] = proposal.aid_int
            except (KeyError, TypeError, ValueError): #pragma: no cover
                pass
        else:
            aid_int = self.proposal_ids.get(ai.__name__, 0) + 1
            aid = "%s-%s" % (tag_name, aid_int)
            proposal.update(aid = aid, aid_int = aid_int)
            self.proposal_ids[ai.__name__] = aid_int


def create_proposal_id(obj, event):
    """ Call an IProposalIds adapter if it exists.
        See IProposalIds for implementation.
    """
    reg = get_current_registry()
    meeting = find_interface(obj, IMeeting)
    proposal_ids = reg.queryAdapter(meeting, IProposalIds, name=meeting.proposal_id_method)
    if proposal_ids:
        proposal_ids.add(obj)


def includeme(config):
    """ Include ProposalIds adapter in registry.
        Call this by running config.include('voteit.core.models.proposal_ids')
    """
    config.add_subscriber(create_proposal_id, [IProposal, IObjectAddedEvent])
    config.registry.registerAdapter(UserIDBasedPropsalIds)
    config.registry.registerAdapter(AgendaItemBasedProposalIds, name = AgendaItemBasedProposalIds.name)
