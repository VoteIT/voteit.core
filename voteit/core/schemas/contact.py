import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core.validators import html_string_validator
from voteit.core.schemas.common import deferred_default_user_fullname
from voteit.core.schemas.common import deferred_default_user_email
from voteit.core import VoteITMF as _


@schema_factory('ContactSchema', title=_("Contact moderator"),
                description = _(u"contact_schema_main_description",
                                default = u"Send a message to the meeting moderators"))
class ContactSchema(colander.MappingSchema):
    name = colander.SchemaNode(colander.String(),
                               title = _(u"Name"),
                               description = _(u"contact_schema_name_description",
                                               default = u"Leave this field empty if you want to be anonymous"),
                               default = deferred_default_user_fullname,
                               validator = colander.Length(max = 100),
                               missing=u"")
    email = colander.SchemaNode(colander.String(),
                               title = _(u"Email"),
                               description = _(u"contact_schema_email_description",
                                               default = u"Leave this field empty if you want to be anonymous. Remember that you won't be able to receive a reply if it's empty!"),
                               default = deferred_default_user_email,
                               validator = colander.Email(),
                               missing=u"") 
    subject = colander.SchemaNode(colander.String(),
                                  title = _(u"Subject"),
                                  validator = html_string_validator,)
    message = colander.SchemaNode(colander.String(),
                                  title = _(u'Message'),
                                  widget = deform.widget.TextAreaWidget(rows=5, cols=40),
                                  validator = html_string_validator,)
