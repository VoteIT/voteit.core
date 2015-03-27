import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.schemas.common import deferred_default_hashtag_text
from voteit.core.schemas.common import random_oid
from voteit.core.validators import NotOnlyDefaultTextValidator


@colander.deferred    
def deferred_discussion_text_validator(node, kw):
    context = kw['context']
    request = kw['request']
    return NotOnlyDefaultTextValidator(context, request, deferred_default_hashtag_text)


class DiscussionPostSchema(colander.Schema):
    text = colander.SchemaNode(colander.String(),
                               title = _(u"Text"),
                               validator = deferred_discussion_text_validator,
                               default = deferred_default_hashtag_text,
                               oid = random_oid,
                               widget = deform.widget.TextAreaWidget(rows=3),)


def includeme(config):
    config.add_content_schema('DiscussionPost', DiscussionPostSchema, ('add','edit'))
