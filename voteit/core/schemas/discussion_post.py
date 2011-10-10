import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import deferred_at_userid_validator
from voteit.core.validators import html_string_validator


@schema_factory('DiscussionPostSchema')
class DiscussionPostSchema(colander.Schema):
    text = colander.SchemaNode(colander.String(),
                               title = _(u"Text"),
                               validator=colander.All(html_string_validator, deferred_at_userid_validator),
                               widget=deform.widget.TextAreaWidget(rows=3, cols=40),)
