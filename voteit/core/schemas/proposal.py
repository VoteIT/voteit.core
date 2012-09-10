import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import deferred_at_enabled_text


@colander.deferred
def deferred_default_proposal_text(node, kw):
    """ Proposals usualy start with "I propose" or something similar.
        This will be the default text, unless there's a hashtag present.
        In that case the hashtag will be default.
    """
    tag = kw.get('tag', u'')
    if tag:
        return u"#%s" % tag
    return _(u"proposal_default_text",
             default = u"proposes ")


#FIXME: Add validation  to make sure that something was entered and the default text isn't returned.
@schema_factory('ProposalSchema')
class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Proposal"),
                                validator = deferred_at_enabled_text,
                                default = deferred_default_proposal_text,
                                widget=deform.widget.TextAreaWidget(rows=3, cols=40),)
    tags = colander.SchemaNode(colander.String(),
                               title = _(u"Tags"),
                               widget=deform.widget.HiddenWidget(),
                               missing=u'')
