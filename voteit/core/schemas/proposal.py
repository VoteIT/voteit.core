import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from translationstring import TranslationString

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IProposal
from voteit.core.validators import AtEnabledTextArea


@colander.deferred
def deferred_default_proposal_text(node, kw):
    """ Proposals usualy start with "I propose" or something similar.
        This will be the default text, unless there's a hashtag present.
        In that case the hashtag will be default.
    """
    context = kw['context']
    tag = kw.get('tag', u'')
    
    if IProposal.providedBy(context):
        # get creator of answered object
        creators = context.get_field_value('creators')
        if creators:
            creator = "@%s" % creators[0]
        else:
            creator = ''
            
        # get tags and make a string of them
        tags = []
        for tag in context._tags:
            tags.append("#%s" % tag)
        
        return "%s:  %s" % (creator, " ".join(tags))
    elif tag:
        return u"#%s" % tag
    
    return _(u"proposal_default_text",
             default = u"proposes ")
    
    
class ProposalTextValidator(object):
    """ Validator which fails if only default text or only tag is pressent
    """
    def __init__(self, context, api, tag):
        self.context = context
        self.api = api
        self.tag = tag

    def __call__(self, node, value):
        # since colander.All doesn't handle deferred validators we call the validator for AtEnabledTextArea here 
        at_enabled_validator = AtEnabledTextArea(self.context)
        at_enabled_validator(node, value)
        
        default = deferred_default_proposal_text(node, {'context':self.context, 'tag':self.tag})
        if isinstance(default, TranslationString):
            default = self.api.translate(default)
        if value.strip() == default.strip():
            raise colander.Invalid(node, _(u"only_default_text_validator_error",
                                           default=u"Only the default content is not valid",))

@colander.deferred    
def deferred_proposal_text_validator(node, kw):
    context = kw['context']
    api = kw['api']
    tag = kw.get('tag', u'')
    return ProposalTextValidator(context, api, tag)


@colander.deferred
def deferred_default_proposal_tags(node, kw):
    context = kw['context']
    if hasattr(context, '_tags'):
        return " ".join(context._tags)
    return ""


@schema_factory('ProposalSchema')
class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Proposal"),
                                validator = deferred_proposal_text_validator,
                                default = deferred_default_proposal_text,
                                widget = deform.widget.TextAreaWidget(rows=3, cols=40),)
    tags = colander.SchemaNode(colander.String(),
                               title = _(u"Tags"),
                               default = deferred_default_proposal_tags,
                               widget = deform.widget.HiddenWidget(),
                               missing = u'')
