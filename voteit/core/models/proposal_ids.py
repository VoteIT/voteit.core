from BTrees.OOBTree import OOBTree
from zope.interface import implementer
from zope.component import adapter
from pyramid.threadlocal import get_current_registry
from pyramid.traversal import find_interface
from repoze.folder.interfaces import IObjectAddedEvent

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IProposalIds


@adapter(IMeeting)
@implementer(IProposalIds)
class ProposalIds(object):
    """ Proposal id adapter.
        See :mod:`voteit.core.models.interfaces.IProposalIds`.
        All methods are documented in the interface of this class.
    """
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

    def add(self, proposal):
        if not proposal.creator:
            raise ValueError("The object %s doesn't have a creator assigned. Can't generate automatic id." % proposal)
        #By convention, first name in list is main creator.
        #No support for many creators yet but it might be implemented.
        creator = proposal.creator[0]
        aid_int = self.proposal_ids.get(creator, 0) + 1
        aid = "%s-%s" % (creator, aid_int)
        proposal.set_field_appstruct({'aid': aid, 'aid_int': aid_int})
        self.proposal_ids[creator] = aid_int


def create_proposal_id(obj, event):
    """ Call an IProposalIds adapter if it exists.
        See IProposalIds for implementation.
    """
    reg = get_current_registry()
    meeting = find_interface(obj, IMeeting)
    proposal_ids = reg.queryAdapter(meeting, IProposalIds)
    if proposal_ids:
        proposal_ids.add(obj)


def includeme(config):
    """ Include ProposalIds adapter in registry.
        Call this by running config.include('voteit.core.models.proposal_ids')
    """
    config.add_subscriber(create_proposal_id, [IProposal, IObjectAddedEvent])
    config.registry.registerAdapter(UserIDBasedPropsalIds)
