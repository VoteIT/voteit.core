import colander
import deform
from arche.interfaces import ISchemaCreatedEvent
from arche.schemas import UserSchema

from voteit.core import VoteITMF as _
#from voteit.core import security
from voteit.core.models.interfaces import IProfileImage
from voteit.core.validators import html_string_validator

#FIXME:
# def came_from_node():
#     return colander.SchemaNode(colander.String(),
#                                missing=u"",
#                                widget = deform.widget.HiddenWidget(),
#                                default=deferred_referer)

@colander.deferred
def profile_image_plugin_choices_widget(node, kw):
    context = kw['context']
    request = kw['request']
    view = kw['view']
    user = view.profile
    plugin_choices = set()
    for (name, adapter) in request.registry.getAdapters((user,), IProfileImage):
        if adapter.is_valid_for_user():
            plugin_choices.add((name, adapter))
    return deform.widget.RadioChoiceWidget(values = plugin_choices, template = "object_radio_choice", readonly_template = "readonly/object_radio_choice")

@colander.deferred
def deferred_local_profile_information_widget(node, kw):
    """ Fetch any keys in auth_domains. """
    context = kw['context']
    choices = [(x, x) for x in context.auth_domains.keys()]
    return deform.widget.CheckboxChoiceWidget(values=choices,
                                              null_value = ())



# @schema_factory('EditUserSchema', title = _(u"Edit user"), description = _(u"Use this form to edit a user"))
# class EditUserSchema(colander.Schema):
#     """ Regular edit. """
#     email = email_node()
#     first_name = first_name_node()
#     last_name = last_name_node()
#     about_me = colander.SchemaNode(colander.String(),
#         title = _(u"About me"),
#         description = _(u"user_about_me_description",
#                         default=u"Please note that anything you type here will be visible to all users in the same meeting as you."),
#         widget = deform.widget.TextAreaWidget(rows=10, cols=60),
#         missing=u"",
#         validator=html_string_validator,)
#     profile_image_plugin = colander.SchemaNode(colander.String(),
#                                                title = _(u"Profile image provider"),
#                                                description = _(u"profile_image_plugin_description",
#                                                                default=u""),
#                                                widget = profile_image_plugin_choices_widget,
#                                                default = deferred_default_profile_image_plugin,) 



# @schema_factory('ManageConnectedProfilesSchema', title = _(u"Manage connected profiles"),
#                 description = _(u"manage_connected_profiles_schema_description",
#                                 default = u"You can remove local authentication information for any connected services. "
#                                 u"This will make you unable to login with that service. "
#                                 u"Be sure to have other means of login in before doing so!"))
# class ManageConnectedProfilesSchema(colander.Schema):
#     auth_domains = colander.SchemaNode(colander.Set(),
#                                        title = u"Remove domains?",
#                                        missing = colander.null,
#                                        widget = deferred_local_profile_information_widget,)

def user_schema_adjustments(schema, event):
    if 'image_data' in schema:
        del schema['image_data']
    schema.add(colander.SchemaNode(colander.String(),
        name = 'about_me',
        title = _(u"About me"),
        description = _(u"user_about_me_description",
                        default=u"Please note that anything you type here will be visible to all users in the same meeting as you."),
        widget = deform.widget.TextAreaWidget(rows=10, cols=60),
        missing=u"",
        validator=html_string_validator,))
    schema.add(colander.SchemaNode(colander.String(),
        name = 'profile_image_plugin',
        title = _(u"Profile image provider"),
        description = _(u"profile_image_plugin_description",
                        default=u""),
        widget = profile_image_plugin_choices_widget,
        default = 'gravatar_profile_image',) )


def includeme(config):
    config.add_subscriber(user_schema_adjustments, [UserSchema, ISchemaCreatedEvent])
    