import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.validators import no_html_validator
from voteit.core.validators import TagValidator
from voteit.core.validators import richtext_validator
from voteit.core.models.interfaces import IProposalIds


_HASHTAG_PATTERN = "^[a-zA-Z0-9\-\_\.]{2,30}$"


@colander.deferred
def ai_tags_widget(node, kw):
    request = kw['request']
    tags = sorted(request.meeting.tags, key=lambda x: x.lower())
    values = [(x, x) for x in tags]
    return deform.widget.CheckboxChoiceWidget(values=values)


class AgendaItemSchema(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        description=_("Try keeping it under 20 characters."),
        validator=no_html_validator, )
    description = colander.SchemaNode(
        colander.String(),
        title=_("Description (In search results and similar)"),
        description=_("Not visible on the agenda page."),
        missing="")
    body = colander.SchemaNode(
        colander.String(),
        title=_("Body"),
        description=_("agenda_item_schema_body",
                      default="Place the the agenda item background information here. "
                              "You can link to external documents and memos. It's also a good "
                              "idea to add an image, it will make it easier for participants "
                              "to quickly see which page they're on."),
        missing="",
        widget=deform.widget.RichTextWidget(options=(('theme', 'advanced'),)),
        validator=richtext_validator, )
    collapsible_limit = colander.SchemaNode(
        colander.Int(),
        title=_("Collapse body texts that are higher than..."),
        widget=deform.widget.SelectWidget(values=(
            # The odd values here are so we can have a sane default
            ('0', _("Off")),
            ('', _("Default (200px)")),
            ('400', "400px"),
            ('600', "600px"),
            ('800', "800px"),
        )),
        missing=None,
    )
    hashtag = colander.SchemaNode(
        colander.String(),
        title=_("Base hashtag for Agenda Item"),
        description=_("ai_hashtag_schema_description",
                      default="Only used by systems that implement agenda based hashtags. "
                              "It's usually a good idea to leave this empty if you "
                              "don't have a special reason to change it. "
                              "(It will use the agenda items name in that case) "
                              "Proposals will be named according to this base tag + a number."),
        missing="",
        validator=colander.Regex(_HASHTAG_PATTERN,
                                 msg=_("Must be a-z, 0-9, or any of '.-_'."))
    )
    tags = colander.SchemaNode(
        colander.Set(),
        title=_("Agenda sorting labels"),
        description=_("ai_schema_tags_description",
                      default="You may add more in the settings menu."),
        widget=ai_tags_widget,
        validator=TagValidator(),
        missing=(),
    )

    def after_bind(self, schema, kw):
        request = kw['request']
        proposal_ids = request.registry.queryAdapter(
            request.meeting, IProposalIds, name=request.meeting.proposal_id_method)
        if proposal_ids is not None and proposal_ids.ai_need_hashtag:
            pass
        else:
            del schema['hashtag']
        if not request.meeting.tags:
            del schema['tags']


def includeme(config):
    config.add_content_schema('AgendaItem', AgendaItemSchema, ('add', 'edit'))
