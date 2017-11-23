import colander
from arche.views.base import DefaultEditForm
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiffText
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
