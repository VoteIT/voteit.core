from uuid import uuid4

import deform
from arche.utils import generate_slug
from arche.views.base import BaseForm
from arche.views.base import BaseView
from arche.views.base import DefaultEditForm
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config
from webhelpers.html.converters import nl2br

from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiffText
from voteit.core.models.interfaces import IProposal
from voteit.core import _


@view_config(context=IAgendaItem,
             name='edit_diff_text',
             permission=security.EDIT,
             renderer='arche:templates/form.pt')
class DiffTextEditForm(DefaultEditForm):
    schema_name='edit_diff_text'
    title = _("Diff text content")

    @reify
    def diff_text(self):
        return IDiffText(self.context)

    def appstruct(self):
        return self.diff_text.get_appstruct(self.schema)

    def save_success(self, appstruct):
        self.diff_text.set_appstruct(appstruct)
        self.flash_messages.add(_("Saved"), type='success')
        return HTTPFound(location=self.request.resource_url(self.context))


@view_config(context=IAgendaItem,
             name='add_diff_proposal',
             permission=security.ADD_PROPOSAL,
             renderer='arche:templates/form.pt')
class AddDiffProposalForm(BaseForm):
    schema_name='add_diff'
    type_name='Proposal'
    title = _("Add new proposal")
    buttons = (deform.Button('next', title=_("Next")),)
    formid = 'add_diff_proposal_form'
    use_ajax = True

    def next_success(self, appstruct):
        print appstruct
        uid = str(uuid4())
        self.request.session[uid] = dict(
            text = appstruct['text'],
            para = int(self.request.GET['para'])-1,
            leadin = appstruct['leadin'],
        )
        url = self.request.resource_url(self.context, 'add_diff_preview',
                                        query={'modal': 1, 'text_uid': uid})
        return HTTPFound(location=url)


@view_config(context=IAgendaItem,
             name='add_diff_preview',
             permission=security.ADD_PROPOSAL,
             renderer='arche:templates/form.pt')
class AddDiffPreviewProposalForm(BaseForm):
    schema_name='add_diff_preview'
    type_name='Proposal'
    title = _("Preview and save")
    buttons = (deform.Button('save', title=_("Save")),)
    formid = 'add_diff_preview_proposal_form'
    use_ajax = True

    ajax_options = """
        {success:
          function () {
            var proposals = $("#ai-proposals [data-load-target]");
            if (proposals.length > 0) {
                var response = voteit.load_target("#ai-proposals [data-load-target]");
                response.done(function() {
                    $('#ai-proposals .list-group-item:last').goTo();
                });
            };
          },
        error:
          function (jqxhr) {
            arche.flash_error(jqxhr);
          }
        }
    """

    @reify
    def diff_text(self):
        return IDiffText(self.context)

    @reify
    def staged_data(self):
        text_uid = self.request.GET.get('text_uid', '')
        data = self.request.session.get(text_uid, None)
        if not data:
            raise HTTPBadRequest("Data not found, try again.")
        return data

    def appstruct(self):
        text = "%s<br/><br/>%s" % (self.staged_data['leadin'], self.staged_data['text'])
        return {'diff_text': self.get_staged_diff(), 'text': text}

    def get_staged_diff(self):
        paragraphs = self.diff_text.get_paragraphs()
        para = self.staged_data['para']
        original = paragraphs[para]
        text = self.staged_data['text']
        return self.diff_text(original, text)

    def save_success(self, appstruct):
        self.flash_messages.add(self.default_success, type="success")
        factory = self.request.content_factories[self.type_name]
        text = "%s\n\n%s" % (self.staged_data['leadin'], self.staged_data['text'])
        appstruct['text'] = text
        appstruct['diff_text'] = self.staged_data['text']
        appstruct['diff_text_para'] = self.staged_data['para']
        obj = factory(**appstruct)
        naming_attr = getattr(obj, 'naming_attr', 'title')
        name = generate_slug(self.context, getattr(obj, naming_attr, ''))
        self.context[name] = obj
        return Response(render("arche:templates/deform/destroy_modal.pt", {}, request = self.request))


@view_config(context=IProposal,
             name='diff_view',
             permission=security.VIEW,
             renderer='voteit.core:templates/snippets/diff_view.pt')
class ProposalDiffView(BaseView):

    @reify
    def diff_text(self):
        return IDiffText(self.request.agenda_item)

    def __call__(self):
        paragraphs = self.diff_text.get_paragraphs()
        try:
            original = paragraphs[self.context.diff_text_para]
        except (TypeError, IndexError):
            raise HTTPNotFound("No diff for this context")
        text = self.diff_text(original, self.context.diff_text)
        return {
            'text': nl2br(text).unescape()
        }
