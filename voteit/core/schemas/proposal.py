from __future__ import unicode_literals

import colander
import deform
from arche.validators import existing_userids
from repoze.workflow import get_workflow

from voteit.core import _
from voteit.core.schemas.common import deferred_default_hashtag_text, MeetingUserReferenceWidget
from voteit.core.schemas.common import random_oid
from voteit.core.validators import NotOnlyDefaultTextValidator
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IProposalIds


@colander.deferred
def deferred_default_proposal_text(node, kw):
    """ Proposals usualy start with "I propose" or something similar.
        This will be the default text, unless there's a hashtag present.
        In that case the hashtag will be default.
        
        This might be used in the context of an agenda item or a proposal.
    """
    request = kw['request']
    hashtag_text = deferred_default_hashtag_text(node, kw)
    proposal_default_text = request.localizer.translate(_(u"proposal_default_text", default = u"proposes"))
    return "%s %s" % (proposal_default_text, hashtag_text)


@colander.deferred    
def deferred_proposal_text_validator(node, kw):
    context = kw['context']
    request = kw['request']
    return NotOnlyDefaultTextValidator(context, request, deferred_default_proposal_text)


class ProposalSchema(colander.Schema):
    text = colander.SchemaNode(
        colander.String(),
        title = _(u"Proposal"),
        description = _("proposal_text_description",
                        default = "A proposal is a statement the meeting can approve or deny. "
            "You may use an at sign to reference a user (ex: 'hello @jane') or a hashtag (ex: '#budget') "
            "to reference or create a tag. All proposals automatically get their own tag."),
        validator = deferred_proposal_text_validator,
        default = deferred_default_proposal_text,
        oid = random_oid,
        widget = deform.widget.TextAreaWidget(rows=3),
    )


@colander.deferred
def proposal_states_widget(node, kw):
    wf = get_workflow(IProposal, 'Proposal')
    state_values = []
    ts = _
    for info in wf._state_info(IProposal):  # Public API goes through permission checker
        item = [info['name']]
        item.append(ts(info['title']))
        state_values.append(item)
    return deform.widget.CheckboxChoiceWidget(values=state_values)


@colander.deferred
def proposal_naming_widget(node, kw):
    request = kw['request']
    values = [(x.name, x.factory.title) for x in request.registry.registeredAdapters()
              if x.provided == IProposalIds]
    return deform.widget.SelectWidget(values=values)


class ProposalSettingsSchema(colander.Schema):
    hide_proposal_states = colander.SchemaNode(
        colander.Set(),
        title=_("Hide proposal states"),
        description=_("hide_proposal_states_description",
                      default="Proposals in these states will be hidden by "
                              "default but can be shown by pressing "
                              "the link below the other proposals. They're not "
                              "by any means invisible to participants."),
        widget=proposal_states_widget,
        default=('retracted', 'denied', 'unhandled'),
    )
    system_userids = colander.SchemaNode(
        colander.List(),
        widget=MeetingUserReferenceWidget(multiple=True),
        validator=existing_userids,
        title=_("System user accounts"),
        description=_("system_userids_description",
                      default="Must be an existing userid. "
                              "If they're added here, moderators can use them "
                              "to add proposals in their name. "
                              "It's good practice to add things like 'propositions', "
                              "'board' or similar."),
        missing=(),
    )
    proposal_id_method = colander.SchemaNode(
        colander.String(),
        title=_("Proposal naming method"),
        widget=proposal_naming_widget,
        missing="",
    )


def includeme(config):
    config.add_schema('Proposal', ProposalSchema, ('add', 'edit'))
    config.add_schema('Proposal', ProposalSettingsSchema, 'settings')
