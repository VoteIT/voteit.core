import re

from BTrees.OOBTree import OOBTree
from zope.interface import implementer
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.helpers import TAG_PATTERN
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.date_time_util import utcnow
from voteit.core.models.workflow_aware import WorkflowAware


_PUBLISHED_MODERATOR_PERMS = (security.VIEW,
                              security.EDIT,
                              security.DELETE,
                              security.RETRACT,
                              security.MODERATE_MEETING,)
_LOCKED_MODERATOR_PERMS = (security.VIEW,
                           security.EDIT,
                           security.DELETE,
                           security.MODERATE_MEETING, )

ACL = {}
ACL['published'] = [(Allow, security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS),
                    (Allow, security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS),
                    (Allow, security.ROLE_OWNER, (security.RETRACT, )),
                    (Allow, security.ROLE_PROPOSE, (security.VIEW,)),
                    (Allow, security.ROLE_DISCUSS, (security.VIEW,)),
                    (Allow, security.ROLE_VOTER, (security.VIEW,)),
                    (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                    DENY_ALL,
                ]
ACL['locked'] = [(Allow, security.ROLE_ADMIN, _LOCKED_MODERATOR_PERMS),
                 (Allow, security.ROLE_MODERATOR, _LOCKED_MODERATOR_PERMS),
                 (Allow, security.ROLE_PROPOSE, (security.VIEW,)),
                 (Allow, security.ROLE_DISCUSS, (security.VIEW,)),
                 (Allow, security.ROLE_VOTER, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                 DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, security.VIEW),
                 (Allow, security.ROLE_MODERATOR, security.VIEW),
                 (Allow, security.ROLE_PROPOSE, (security.VIEW,)),
                 (Allow, security.ROLE_DISCUSS, (security.VIEW,)),
                 (Allow, security.ROLE_VOTER, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, security.VIEW),
                 DENY_ALL,
                ]
ACL['private'] = [(Allow, security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS),
                  (Allow, security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS),
                  DENY_ALL,
                  ]


#@content_factory('Proposal', title=_(u"Proposal"))
@implementer(IProposal, ICatalogMetadataEnabled)
class Proposal(BaseContent, WorkflowAware):
    """ Proposal content type.
        See :mod:`voteit.core.models.interfaces.IProposal`.
        All methods are documented in the interface of this class.
    """
    type_name = 'Proposal'
    type_title = _(u"Proposal")
    #allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_PROPOSAL
    schemas = {'add': 'ProposalSchema',
               'edit': 'ProposalSchema'}
    custom_mutators = {'title': '_set_title'}

    @property
    def __acl__(self):
        ai = find_interface(self, IAgendaItem)
        ai_state = ai.get_workflow_state()
        #If ai is private, use private
        if ai_state == 'private':
            return ACL['private']
        state = self.get_workflow_state()
        if state == 'published':
            return ACL['published']
        #Check if AI is open.
        if ai_state == 'closed':
            return ACL['closed']
        return ACL['locked']

    def _get_title(self):
        return self.get_field_value('title', u"")
    
    def _set_title(self, value, key=None):
        self.field_storage['title'] = value
    
    title = property(_get_title, _set_title)

    @property
    def mentioned(self):
        try:
            return self.__mentioned__
        except AttributeError:
            self.__mentioned__ = OOBTree()
            return self.__mentioned__

    def add_mention(self, userid):
        self.mentioned[userid] = utcnow()

    def get_tags(self, default = ()):
        tags = []
        for matchobj in re.finditer(TAG_PATTERN, self.title):
            tag = matchobj.group('tag').lower()
            if tag not in tags:
                tags.append(tag)
        aid = self.get_field_value('aid', None)
        if aid is not None and aid not in tags:
            tags.append(aid)
        return tags and tags or default

    @property
    def tags(self): #arche compat
        return self.get_tags()
    @tags.setter
    def tags(self, value):
        print "Tags shouldn't be set like this"


def includeme(config):
    config.add_content_factory(Proposal, addable_to = 'AgendaItem')
    