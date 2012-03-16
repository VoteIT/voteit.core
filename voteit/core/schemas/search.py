import colander
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _


@schema_factory('SearchSchema', title = _(u"Search"))
class SearchSchema(colander.Schema):
    query = colander.SchemaNode(colander.String(),
                                description = _(u"search_schema_query_description",
                                                default = u"You can use '*' as wildcard or '?' as a single unknown charracter."),
                                missing = u"",)
