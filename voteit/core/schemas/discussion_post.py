import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.schemas.common import deferred_default_hashtag_text
#from voteit.core.schemas.common import deferred_default_tags
from voteit.core.schemas.common import random_oid
from voteit.core.validators import NotOnlyDefaultTextValidator


@colander.deferred    
def deferred_discussion_text_validator(node, kw):
    context = kw['context']
    request = kw['request']
    return NotOnlyDefaultTextValidator(context, request, deferred_default_hashtag_text)


@schema_factory('DiscussionPostSchema')
class DiscussionPostSchema(colander.Schema):
    text = colander.SchemaNode(colander.String(),
                               title = _(u"Text"),
                               validator = deferred_discussion_text_validator,
                               default = deferred_default_hashtag_text,
                               oid = random_oid,
                               widget = deform.widget.TextAreaWidget(rows=3),)
#     tags = colander.SchemaNode(colander.String(),
#                                title = _(u"Tags"),
#                                default = deferred_default_tags,
#                                widget = deform.widget.HiddenWidget(),
#                                oid = random_oid,
#                                missing = u'')


def includeme(config):
    config.add_content_schema('DiscussionPost', DiscussionPostSchema, ('add','edit'))
