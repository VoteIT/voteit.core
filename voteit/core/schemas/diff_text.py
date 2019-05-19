from __future__ import unicode_literals

import colander
import deform
from arche.schemas import maybe_modal_form
from pyramid.httpexceptions import HTTPBadRequest

from voteit.core import _
from voteit.core.models.interfaces import IDiffText
from voteit.core.schemas.common import collapsible_limit_node
from voteit.core.schemas.proposal import ProposalSchema
from voteit.core.validators import no_html_validator


class DiffTextSettingsSchema(colander.Schema):
    diff_text_enabled = colander.SchemaNode(
        colander.Bool(),
        title = _("Enable diff text proposals"),
        description = _("diff_text_enabled_description",
                        default="Makes it possible to add a text chunk "
                        "and then write proposals on changes in that text.")
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
        missing="",
        widget=deform.widget.TextAreaWidget(rows=12),
        validator=no_html_validator,
    )
    hashtag = colander.SchemaNode(
        colander.String(),
        title=_("Base hashtag for paragraphs"),
        description=_("Use lowercase a-z. All paragraphs will be marked with this tag and then a number. "
                      "All new proposals will use it as a mandatory hashtag."),
        default=default_hashtag_name,
        valdator=colander.Regex("^[a-z]{2,15}$", msg=_("Only lowercase a-z please")),
    )
    collapsible_limit = collapsible_limit_node()


def _get_request_para(request):
    para = request.params.get('para', None)
    if not para:
        return
    try:
        para = int(para)
    except TypeError:
        return
    return para


@colander.deferred
def default_diff_prop_text(node, kw):
    request = kw['request']
    diff_text = IDiffText(request.agenda_item)
    para = _get_request_para(request)
    if para == None:
        return ''
    paragraphs = diff_text.get_paragraphs()
    try:
        return paragraphs[para-1]
    except IndexError:
        return ''


@colander.deferred
def default_leadin(node, kw):
    request = kw['request']
    para = _get_request_para(request)
    if para == None:
        raise HTTPBadRequest("Restart form")
    diff_text = IDiffText(request.agenda_item)
    hashtag = "%s-%s" % (diff_text.hashtag, para)
    return request.localizer.translate(
        _("default_lead_in",
          default="proposes changes to #${hashtag}:",
          mapping={'hashtag': hashtag})
    )


@colander.deferred
class LeadInValidator(object):

    def __init__(self, node, kw):
        self.request = kw['request']

    def __call__(self, node, value):
        para = _get_request_para(self.request)
        if para == None:
            raise HTTPBadRequest("Restart form")
        diff_text = IDiffText(self.request.agenda_item)
        hashtag = "#%s-%s" % (diff_text.hashtag, para)
        if hashtag not in value:
            msg = _("Please keep the hashtag ${hashtag} in your lead-in.",
                    mapping={'hashtag': hashtag})
            raise colander.Invalid(node, msg)
        pass


@colander.deferred
class DiffProposalValidator(object):

    def __init__(self, node, kw):
        self.request = kw['request']

    def __call__(self, node, value):
        #FIXME: Add other validators from proposals
        default_text = default_diff_prop_text(node, {'request': self.request})
        if default_text.replace('\r\n', '\n') == value.replace('\r\n', '\n'):
            raise colander.Invalid(node, _("You haven't changed anything"))
        no_html_validator(node, value)


class AddDiffProposalSchema(colander.Schema):
    widget = maybe_modal_form
    leadin = colander.SchemaNode(
        colander.String(),
        title=_("Lead-in"),
        default=default_leadin,
        validator=LeadInValidator,
    )
    text = colander.SchemaNode(
        colander.String(),
        default=default_diff_prop_text,
        validator=DiffProposalValidator,
        widget=deform.widget.TextAreaWidget(rows=4),
    )


@colander.deferred
def staged_text_change(node, kw):
    request = kw['request']
    text_uid = request.GET.get('text_uid', '')
    data = request.session.get(text_uid, None)
    if not data:
        raise HTTPBadRequest("No data found, restart procedure")
    return data['text']


class AddDiffPreviewSchema(ProposalSchema):
    widget = maybe_modal_form
    leadin = colander.SchemaNode(
        colander.String(),
        title=_("Lead-in"),
        default=default_leadin,
        widget=deform.widget.TextInputWidget(readonly=True),
        missing="",
        rows=4,
    )
    text = colander.SchemaNode(
        colander.String(),
        widget = deform.widget.HiddenWidget(),
        missing="",
    )
    diff_text = colander.SchemaNode(
        colander.String(),
        missing="",
        widget=deform.widget.TextInputWidget(
            readonly = True,
            readonly_template = 'readonly/diff_html',
        ),
    )


def includeme(config):
    config.add_schema('Meeting', DiffTextSettingsSchema, 'diff_text_settings')
    config.add_schema('AgendaItem', DiffTextContentSchema, 'edit_diff_text')
    config.add_schema('Proposal', AddDiffProposalSchema, 'add_diff')
    config.add_schema('Proposal', AddDiffPreviewSchema, 'add_diff_preview')
