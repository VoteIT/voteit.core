import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from translationstring import TranslationString

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IProposal
from voteit.core.validators import AtEnabledTextArea


@colander.deferred
def deferred_default_discussion_text(node, kw):
    """ If this is a reply to something else, the default value will be the hashtag
        of that message.
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
    
    return ''

class DiscussionTextValidator(object):
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
        
        default = deferred_default_discussion_text(node, {'context':self.context, 'tag':self.tag})
        if isinstance(default, TranslationString):
            default = self.api.translate(default)
        if value.strip() == default.strip():
            raise colander.Invalid(node, _(u"only_default_text_validator_error",
                                           default=u"Only the default content is not valid",))

@colander.deferred    
def deferred_discussion_text_validator(node, kw):
    context = kw['context']
    api = kw['api']
    tag = kw.get('tag', u'')
    return DiscussionTextValidator(context, api, tag)


@colander.deferred
def deferred_default_discussion_tags(node, kw):
    context = kw['context']
    if hasattr(context, '_tags'):
        return " ".join(context._tags)
    return ""


@schema_factory('DiscussionPostSchema')
class DiscussionPostSchema(colander.Schema):
    text = colander.SchemaNode(colander.String(),
                               title = _(u"Text"),
                               validator = deferred_discussion_text_validator,
                               default = deferred_default_discussion_text,
                               widget = deform.widget.TextAreaWidget(rows=3, cols=40),)
    tags = colander.SchemaNode(colander.String(),
                               title = _(u"Tags"),
                               default = deferred_default_discussion_tags,
                               widget = deform.widget.HiddenWidget(),
                               missing = u'')
