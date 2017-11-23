from __future__ import unicode_literals

import colander
import deform

from voteit.core import _


class DiffTextSettingsSchema(colander.Schema):
    diff_text_enabled = colander.SchemaNode(
        colander.Bool(),
    )


@colander.deferred
def default_hashtag_name(node, kw):
    request = kw['request']
    return request.localizer.translate(_("paragraph"))


class DiffTextContentSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        missing="",
    )
    text = colander.SchemaNode(
        colander.String(),
        title=_("Text body"),
        description=_(
            "diff_text_schema_text_description",
            default="Each paragraph will have its own hashtag. "
                    "Separate paragraphs with 2 new lines."
        ),
        widget=deform.widget.TextAreaWidget(rows=12),
    )
    hashtag = colander.SchemaNode(
        colander.String(),
        title=_("Base hashtags for paragraphs"),
        description=_("Use lowercase a-z. All paragraphs will be marked with this tag and then a number. "
                      "All new proposals will use it as a mandatory hashtag."),
        default=default_hashtag_name,
        valdator=colander.Regex("^[a-z]{2,15}$", msg=_("Only lowercase a-z please")),
    )


def includeme(config):
    config.add_schema('Meeting', DiffTextSettingsSchema, 'diff_text_settings')
    config.add_schema('AgendaItem', DiffTextContentSchema, 'edit_diff_text')
