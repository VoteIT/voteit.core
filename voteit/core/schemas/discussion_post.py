import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import deferred_at_enabled_text


@colander.deferred
def deferred_default_discussion_text(node, kw):
    """ If this is a reply to something else, the default value will be the hashtag
        of that message.
    """
    tag = kw.get('tag', u'')
    return tag and u"#%s" % tag or u""


@schema_factory('DiscussionPostSchema')
class DiscussionPostSchema(colander.Schema):
    text = colander.SchemaNode(colander.String(),
                               title = _(u"Text"),
                               default = deferred_default_discussion_text,
                               validator = deferred_at_enabled_text,
                               widget = deform.widget.TextAreaWidget(rows=3, cols=40),)
    tags = colander.SchemaNode(colander.String(),
                               title = _(u"Tags"),
                               widget = deform.widget.HiddenWidget(),
                               missing = u'')
