import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.validators import NotOnlyDefaultTextValidator
from voteit.core.schemas.common import deferred_default_tags
from voteit.core.schemas.common import deferred_default_hashtag_text


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


class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Proposal"),
                                validator = deferred_proposal_text_validator,
                                default = deferred_default_proposal_text,
                                widget = deform.widget.TextAreaWidget(rows=3),)
    tags = colander.SchemaNode(colander.String(),
                               title = _(u"Tags"),
                               default = deferred_default_tags,
                               widget = deform.widget.HiddenWidget(),
                               missing = u'')

def includeme(config):
    config.add_content_schema('Proposal', ProposalSchema, ('add', 'edit'))
