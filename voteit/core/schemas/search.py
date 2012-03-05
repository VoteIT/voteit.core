import colander
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _


@schema_factory('SearchSchema', title = _(u"Search"))
class SearchSchema(colander.Schema):
    query = colander.SchemaNode(colander.String(),
                                missing = u"",)
