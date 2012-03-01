import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core.validators import html_string_validator
from voteit.core import VoteITMF as _


@schema_factory('ContactSchema', title=_("Contact"))
class ContactSchema(colander.MappingSchema):
    name = colander.SchemaNode(colander.String(),
                               title = _(u"Name"),
                               description = _(u"Leave this field empty you want to be anonymous"),
                               missing=u"")
    email = colander.SchemaNode(colander.String(),
                               title = _(u"Email"),
                               description = _(u"Leave this field empty you want to be anonymous"),
                               missing=u"") 
    subject = colander.SchemaNode(colander.String(),
                                  title = _(u"Subject"),
                                  validator = html_string_validator,)
    message = colander.SchemaNode(colander.String(),
                                  title = _(u'Message'),
                                  widget = deform.widget.TextAreaWidget(rows=5, cols=40),
                                  validator = html_string_validator,)