import colander
import deform

from voteit.core.validators import html_string_validator
from voteit.core.validators import deferred_at_userid_validator
from voteit.core import VoteITMF as _
from betahaus.pyracont.decorators import schema_factory


@schema_factory('ProposalSchema')
class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"I propose:"),
                                validator=colander.All(html_string_validator, deferred_at_userid_validator),
                                widget=deform.widget.TextAreaWidget(rows=3, cols=40),)
