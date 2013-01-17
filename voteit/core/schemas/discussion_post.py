import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import NotOnlyDefaultTextValidator
from voteit.core.schemas.common import deferred_default_tags
from voteit.core.schemas.common import deferred_default_hashtag_text


@colander.deferred    
def deferred_discussion_text_validator(node, kw):
    context = kw['context']
    api = kw['api']
    return NotOnlyDefaultTextValidator(context, api, deferred_default_hashtag_text)


@schema_factory('DiscussionPostSchema')
class DiscussionPostSchema(colander.Schema):
    text = colander.SchemaNode(colander.String(),
                               title = _(u"Text"),
                               validator = deferred_discussion_text_validator,
                               default = deferred_default_hashtag_text,
                               widget = deform.widget.TextAreaWidget(rows=3),)
    tags = colander.SchemaNode(colander.String(),
                               title = _(u"Tags"),
                               default = deferred_default_tags,
                               widget = deform.widget.HiddenWidget(),
                               missing = u'')
