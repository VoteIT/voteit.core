from BTrees.OOBTree import OOBTree
from zope.interface import implements
from zope.component import adapts

from voteit.core.models.interfaces import IProposalIds
from voteit.core.models.interfaces import IMeeting


class ProposalIds(object):
    """ Proposal id adapter.
        See :mod:`voteit.core.models.interfaces.IProposalIds`.
        All methods are documented in the interface of this class.
    """
    implements(IProposalIds)
    adapts(IMeeting)
    
    def __init__(self, context):
        """ Context to adapt """
        self.context = context
    
    @property
    def _proposal_ids(self):
        """ Acts as a storage.
        """
        try:
            return self.context.__proposal_ids__
        except AttributeError:
            self.context.__proposal_ids__ = OOBTree()
            return self.context.__proposal_ids__
    
    def add(self, userid, value):
        self._proposal_ids[userid] = value

    def get(self, userid):
        if userid in self._proposal_ids:
            return self._proposal_ids[userid]
        return None


def includeme(config):
    """ Include ProposalIds adapter in registry.
        Call this by running config.include('voteit.core.models.proposal_ids')
    """
    config.registry.registerAdapter(ProposalIds, (IMeeting,), IProposalIds)
