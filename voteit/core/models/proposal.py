from __future__ import unicode_literals

from arche.resources import ContextACLMixin
from arche.security import get_acl_registry
from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq
from six import string_types
from zope.interface import implementer

from voteit.core import _
from voteit.core import security
from voteit.core.helpers import strip_and_truncate
from voteit.core.helpers import tags_from_text
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.workflow_aware import WorkflowCompatMixin


@implementer(IProposal)
class Proposal(BaseContent, ContextACLMixin, WorkflowCompatMixin):
    """ Proposal content type.
        See :mod:`voteit.core.models.interfaces.IProposal`.
        All methods are documented in the interface of this class.
    """
    type_name = 'Proposal'
    type_title = _("Proposal")
    add_permission = security.ADD_PROPOSAL
    css_icon = 'glyphicon glyphicon-exclamation-sign'

    @property
    def __acl__(self):
        ai = find_interface(self, IAgendaItem)
        ai_state = ai.wf_state
        acl = get_acl_registry()
        #If ai is private, use private
        if ai_state == 'private':
            return acl.get_acl('Proposal:private')
        if ai_state == 'closed':
            return acl.get_acl('Proposal:closed')
        return super(Proposal, self).__acl__

    @property
    def title(self):
        return strip_and_truncate(self.text, limit = 100, symbol = '')
    @title.setter
    def title(self, value):
        raise NotImplementedError("Tried to set title on Proposal")

    @property
    def text(self):
        return self.get_field_value('text', '')
    @text.setter
    def text(self, value):
        self.set_field_value('text', value)

    @property
    def tags(self): #arche compat
        tags = tags_from_text(self.text)
        if self.diff_text_leadin:
            for tag in tags_from_text(self.diff_text_leadin):
                if tag not in tags:
                    tags.append(tag)
        aid = self.get_field_value('aid', None)
        if aid is not None and aid not in tags:
            tags.append(aid)
        return list(tags)
    @tags.setter
    def tags(self, value):
        print "Tags shouldn't be set like this"

    @property
    def aid(self): #arche compat
        return self.get_field_value('aid', '')
    @aid.setter
    def aid(self, value):
        self.set_field_value('aid', value)

    @property #arche compat
    def aid_int(self):
        return self.get_field_value('aid_int', None)
    @aid_int.setter
    def aid_int(self, value):
        self.set_field_value('aid_int', value)

    @property
    def diff_text_leadin(self):
        return self.get_field_value('diff_text_leadin', None)
    @diff_text_leadin.setter
    def diff_text_leadin(self, value):
        assert isinstance(value, string_types)
        self.set_field_value('diff_text_leadin', value)

    @property
    def diff_text_para(self):
        """ Which paragraph this is a diff against. """
        return self.get_field_value('diff_text_para', None)
    @diff_text_para.setter
    def diff_text_para(self, value):
        assert isinstance(value, int)
        self.set_field_value('diff_text_para', value)


def guard_proposals_that_are_part_of_a_poll(request, context):
    ai = find_interface(context, IAgendaItem)
    query = Eq('path', resource_path(ai)) & Eq('type_name', 'Poll')
    docids = request.root.catalog.query(query)[1]
    found = []
    for poll in request.resolve_docids(docids, perm=None):
        if context.uid in poll.proposals:
            found.append(poll)
    return found


def includeme(config):
    config.add_content_factory(Proposal, addable_to = 'AgendaItem')
    # Ref guard for proposals
    config.add_ref_guard(
        guard_proposals_that_are_part_of_a_poll,
        requires=(IProposal,),
        catalog_result=False,
        title=_("Proposal is a part of poll(s)"),
    )
