import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import deferred_at_enabled_text
from voteit.core.widgets import TextAreaStripLinksWidget


@schema_factory('DiscussionPostSchema')
class DiscussionPostSchema(colander.Schema):
    text = colander.SchemaNode(colander.String(),
                               title = _(u"Text"),
                               validator=deferred_at_enabled_text,
                               widget=TextAreaStripLinksWidget(rows=3, cols=40),)
