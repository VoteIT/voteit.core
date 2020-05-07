from hashlib import md5

import colander
import deform
from arche.interfaces import ISchemaCreatedEvent
from arche.schemas import SiteSettingsSchema
from zope.interface import implementer
from zope.component import adapter

from voteit.core import _
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IProfileImage


@implementer(IProfileImage)
@adapter(IUser)
class GravatarProfileImagePlugin(object):
    name = u"gravatar_profile_image"
    title = _("Gravatar")
    description = _(
        "profile_gravatar_explanation",
        default='Profile image from <a href="http://www.gravatar.com" target="_blank">Gravatar network</a>. '
        "It's taken from your current email address. If you want to change the picture, simply go to "
        "the Gravatar site and change your picture for the email you use in VoteIT.",
    )

    def __init__(self, context):
        self.context = context

    def url(self, size, request):
        url = "https://secure.gravatar.com/avatar/"
        email = self.context.get_field_value("email", "").strip().lower()
        if email:
            url += md5(email).hexdigest()
        url += "?s=%s" % size
        gt = request.root.site_settings.get(
            "gravatar_default_type",
            request.registry.settings.get("voteit.gravatar_default", "robohash"),
        )
        url += "&d=%s" % gt

        return url

    def is_valid_for_user(self):
        return True


_GRAVATAR_CHOICES = (
    (
        "mp",
        _(
            "a simple, cartoon-style silhouetted outline of a person (does not vary by email hash)"
        ),
    ),
    ("identicon", _("A geometric pattern based on an email hash")),
    ("monsterid", _("A generated 'monster' with different colors, faces, etc")),
    ("wavatar", _("A generated faces with differing features and backgrounds")),
    ("retro", _("Awesome generated, 8-bit arcade-style pixelated faces")),
    ("robohash", _("A generated robot with different colors, faces, etc")),
)


def insert_gravatar_settings(schema, event):
    try:
        default_type = event.request.registry.settings.get(
            "voteit.gravatar_default", "robohash"
        )
    except AttributeError:
        default_type = "robohash"
    schema.add(
        colander.SchemaNode(
            colander.String(),
            default=default_type,
            name="gravatar_default_type",
            title=_("Gravatar default type"),
            description=_(
                "gravatar_default_description",
                default="What to use in case users don't have a gravatar image registered. "
                "See: ${url} for more information and examples.",
                mapping={"url": "https://gravatar.com/site/implement/images"},
            ),
            widget=deform.widget.RadioChoiceWidget(values=_GRAVATAR_CHOICES),
        )
    )


def includeme(config):
    """ Include gravatar plugin
    """
    config.registry.registerAdapter(
        GravatarProfileImagePlugin, name=GravatarProfileImagePlugin.name
    )
    config.add_subscriber(
        insert_gravatar_settings, [SiteSettingsSchema, ISchemaCreatedEvent]
    )
