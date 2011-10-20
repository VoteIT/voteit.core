import colander
import deform
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.view import view_config
from pyramid.url import resource_url
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IExportImport
from voteit.core.security import MANAGE_SERVER
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_download
from voteit.core.models.schemas import button_save
from pyramid.security import has_permission


class ExportImportView(BaseView):
    """ Handle export and import of database objects. """
    
    @view_config(name = '_export', context = IBaseContent, renderer = "templates/base_edit.pt")
    def export_view(self):
        redirect_url = resource_url(self.context, self.request)
        if not has_permission(MANAGE_SERVER, self.api.root, self.request):
            raise HTTPForbidden("You're not allowed to access this view")
        export_import = self.request.registry.queryAdapter(self.api.root, IExportImport)
        if not export_import:
            msg = _(u"ExportImport component not included in VoteIT. You need to register it to use this.")
            self.api.flash_messages.add(msg, type = 'error')
            return HTTPFound(location=redirect_url)

        form = deform.Form(colander.Schema(), buttons=(button_download, button_cancel))
        self.api.register_form_resources(form)

        if 'download' in self.request.POST:
            return export_import.download_export(self.context)
        
        if 'cancel' in self.request.POST:
            self.api.flash_messages.add(_(u"Canceled"))
            return HTTPFound(location=redirect_url)

        #No action
        msg = _(u"Export current context")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    @view_config(name = '_import', context = IBaseContent, renderer = "templates/base_edit.pt")
    def import_view(self):
        if not has_permission(MANAGE_SERVER, self.api.root, self.request):
            raise HTTPForbidden("You're not allowed to access this view")
        redirect_url = resource_url(self.context, self.request)
        export_import = self.request.registry.queryAdapter(self.api.root, IExportImport)
        if not export_import:
            msg = _(u"ExportImport component not included in VoteIT. You need to register it to use this.")
            self.api.flash_messages.add(msg, type = 'error')
            return HTTPFound(location=redirect_url)
        schema = createSchema('ImportSchema').bind(context = self.context, request = self.request)
        form = deform.Form(schema, buttons=(button_save, button_cancel))
        self.api.register_form_resources(form)

        if 'save' in self.request.POST:
            controls = self.request.params.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response

            name = appstruct['name']
            filedata = appstruct['upload']
            export_import.import_data(self.context, name, filedata)
            filedata.clear()
            self.api.flash_messages.add(_(u"Created new objects from import"))
            return HTTPFound(location=redirect_url)

        if 'cancel' in self.request.POST:
            self.api.flash_messages.add(_(u"Canceled"))
            return HTTPFound(location=redirect_url)

        #No action
        msg = _(u"Import file to current context")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response
