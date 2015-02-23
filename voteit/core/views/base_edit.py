from __future__ import unicode_literals
import urllib

from betahaus.pyracont.factories import createSchema
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.session import check_csrf_token
from pyramid.view import view_config
from pyramid_deform import FormView
from repoze.workflow.workflow import WorkflowError
import colander

from voteit.core import VoteITMF as _
from voteit.core.models.arche_compat import createContent
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IFlashMessages
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUsers
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.models.schemas import add_came_from
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_delete
from voteit.core.models.schemas import button_save
from voteit.core.security import DELETE
from voteit.core.security import EDIT
from voteit.core.views.api import APIView


DEFAULT_TEMPLATE = "voteit.core:views/templates/base_edit.pt"


class BaseEdit(object):
    """ Default edit class. Subclass this to create edit views. """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.response = {}
        self.response['api'] = self.api = APIView(context, request)
        self.api.include_needed(context, request, self)


class ArcheFormCompat(object):

    def appstruct(self):
        return self.context.get_field_appstruct(self.schema)

    def save_success(self, appstruct):
        self.flash_messages.add(self.default_success)
        self.context.set_field_appstruct(appstruct)
        return HTTPFound(location = self.request.resource_url(self.context))


class BaseForm(BaseEdit, FormView):
    """ This version work with pyramid_deform.
    """
    default_success = _("Done")
    default_cancel = _("Canceled")
    buttons = (button_save, button_cancel,)
    check_csrf = True
    readonly = False
    schema = None #Good testing injection point too

    def __init__(self, context, request):
        super(BaseForm, self).__init__(context, request)
        self.schema = self.get_schema()

    def __call__(self):
        if self.check_csrf:
            add_csrf_token(self.context, self.request, self.schema)
        return super(BaseForm, self).__call__()

    def get_schema(self):
        """ Get schema instance for this form. """
        if self.schema is not None:
            return self.schema
        raise NotImplementedError() #pragma : no cover

    @property
    def form_options(self):
        return {'action': self.request.url,}

    def get_bind_data(self):
        return {'context': self.context, 'request': self.request, 'view': self, 'api': self.api}

    def appstruct(self):
        """ Return appstruct, ie a dict of current values for this schema.
            On add schemas, it should be blank since you're adding something to an existing context.
        """
        return self.context.get_field_appstruct(self.schema)

    def cancel(self, *args):
        self.api.flash_messages.add(self.default_cancel)
        return HTTPFound(location = self.request.resource_url(self.context))
    cancel_success = cancel_failure = cancel

    def before(self, form):
        """ Runs before form is actually rendered. If you override this, make sure
            to call superclass to include needed resources.
            Will also check csrf_token if something was posted and the attribute check_csrf is true.
        """
        if self.check_csrf == True and self.request.method == 'POST':
            check_csrf_token(self.request)
        self.api.register_form_resources(form)

    def tpl_data(self):
        """ Returns template data.
        """
        return {'api': self.api,
                'view': self,
                'context': self.context,
                'request': self.request}

    def show(self, form):
        appstruct = self.appstruct()
        if appstruct is None:
            appstruct = {}
        rendered = form.render(appstruct = appstruct,
                               readonly = self.readonly)
        response = {'form': rendered}
        response.update(self.tpl_data())
        return response

    def failure(self, e):
        response = super(BaseForm, self).failure(e)
        response.update(self.tpl_data())
        return response


#@view_config(context=IBaseContent, name="add", renderer=DEFAULT_TEMPLATE)
class DefaultAddForm(BaseForm):
    buttons = (button_add, button_cancel,)

    @property
    def content_type(self):
        return self.request.params.get('content_type')

    def get_schema(self):
        schema_name = self.api.get_schema_name(self.content_type, 'add')
        return createSchema(schema_name)

    def __call__(self):
        #Permission check must be performed within this form since permissions differ on add views
        add_permission = self.api.content_types_add_perm(self.content_type)
        #if not has_permission(add_permission, self.context, self.request):
        if not self.api.context_has_permission(add_permission, self.context):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % self.content_type)
        response =  super(DefaultAddForm, self).__call__()
        if self.content_type == 'AgendaItem' and isinstance(response, dict):
            response['tabs'] = self.api.render_single_view_component(self.context, self.request,
                                                                     'tabs', 'manage_agenda')
        return response

    def appstruct(self):
        return {}

    def add_success(self, appstruct):
        factory = self.api.get_content_factory(self.content_type)
        obj = createContent(self.content_type, **appstruct)
        name = obj.suggest_name(self.context)
        self.context[name] = obj
        #Success, redirect
        url = self.request.resource_url(obj)
        self.api.flash_messages.add(_("Successfully added"))
        return HTTPFound(location=url)


#@view_config(context=ISiteRoot, name="add", renderer=DEFAULT_TEMPLATE, request_param = "content_type=Meeting")
class AddMeetingForm(DefaultAddForm):

    def add_success(self, appstruct):
        copy_users_and_perms = appstruct.pop('copy_users_and_perms', False)
        obj = createContent(self.content_type, **appstruct)
        name = obj.suggest_name(self.context)
        self.context[name] = obj
        if copy_users_and_perms:
            obj.copy_users_and_perms(copy_users_and_perms)
            self.api.flash_messages.add(_("Users and their permissions successfully copied"))
        else:
            self.api.flash_messages.add(_("Successfully added"))
        return HTTPFound(location = self.request.resource_url(obj))


#@view_config(context=IUsers, name="add", renderer=DEFAULT_TEMPLATE, request_param = "content_type=User")
class AddUserForm(DefaultAddForm):

    def add_success(self, appstruct):
        #Userid and name should be consistent
        name = appstruct.pop('userid')
        #creators takes care of setting the role owner as well as adding it to creators attr.
        obj = createContent('User', creators=[name], **appstruct)
        self.context[name] = obj
        self.api.flash_messages.add(_(u"Successfully added"))
        return HTTPFound(location = self.request.resource_url(obj))


#@view_config(context=IBaseContent,
#             name="edit",
#             renderer=DEFAULT_TEMPLATE,
#             permission=EDIT)
class DefaultEditForm(BaseForm):
    buttons = (button_save, button_cancel,)

    def get_schema(self):
        schema_name = self.api.get_schema_name(self.context.content_type, 'edit')
        schema = createSchema(schema_name)
        add_came_from(self.context, self.request, schema)
        return schema

    def save_success(self, appstruct):
        came_from = appstruct.pop('came_from', None)
        if came_from:
            url = urllib.unquote(came_from)
        elif self.context.content_type == 'Poll':
            url = self.request.resource_url(self.context.__parent__, anchor = self.context.uid)
        else:
            url = self.request.resource_url(self.context)
        updated = self.context.set_field_appstruct(appstruct)
        if updated:
            self.api.flash_messages.add(_("Successfully updated"))
        else:
            self.api.flash_messages.add(_("Nothing updated"))
        return HTTPFound(location = url)


@view_config(name = 'delete', context = ISiteRoot)
@view_config(name = 'delete', context = IUsers)
def no_delete(*args):
    raise HTTPForbidden(_("Can't delete this content type"))


# @view_config(context=IBaseContent,
#              name="delete",
#              permission=DELETE,
#              renderer=DEFAULT_TEMPLATE)
class DefaultDeleteForm(BaseForm):
    buttons = (button_delete, button_cancel,)

    def __call__(self):
        if self.context.content_type == 'User':
            #Find any content created by this user. In case there's some, abort delete
            res = self.api.search_catalog(creators = self.context.userid)[0]
            if res.total > 1:
                raise HTTPForbidden(_("deleting_user_notice",
                                      default = "Deleting users that are main creators of content isn't supported yet. "
                                      "Delete their content first."))
        if self.context.content_type == 'Proposal':
            used_in_polls = []
            ai = self.context.__parent__
            for poll in ai.get_content(content_type = 'Poll'):
                if self.context.uid in poll.proposal_uids:
                    used_in_polls.append("'%s'" % poll.title)
            if used_in_polls:
                msg = _("deleting_proposals_used_in_polls_not_allowed_error",
                        default = "You can't remove this proposal - it's used within the following polls: ${poll_titles}",
                        mapping = {'poll_titles': ", ".join(used_in_polls)})
                self.api.flash_messages.add(msg, type = 'error', close_button = False)
                raise HTTPFound(location = self.request.resource_url(ai))
        if self.request.method != 'POST':
            msg = _("delete_form_notice",
                    default = "Are you sure you want to delete '${display_name}' with title: ${title}?",
                    mapping = {'display_name': self.api.translate(self.context.display_name),
                               'title': self.context.title})
            self.api.flash_messages.add(msg, close_button = False)
        return super(DefaultDeleteForm, self).__call__()

    def get_schema(self):
        schema = colander.Schema()
        add_came_from(self.context, self.request, schema)
        return schema

    def delete_success(self, appstruct):
        parent = self.context.__parent__
        del parent[self.context.__name__]
        self.api.flash_messages.add(_("Deleted"))
        url = self.request.resource_url(parent)
        came_from = self.request.POST.get('came_from', None)
        if came_from:
            url = urllib.unquote(came_from)
        return HTTPFound(location=url)


@view_config(context=IWorkflowAware, name="state")
def state_change(context, request):
    """ Change workflow state for context.
        Note that permission checks are done by the workflow machinery.
        In case something goes wrong (for instance wrong permission) a
        WorkflowError will be raised.
    """
    state = request.params.get('state')
    try:
        context.set_workflow_state(request, state)
    except WorkflowError as exc:
        raise HTTPForbidden(str(exc))
    fm = IFlashMessages(request)
    fm.add(_(context.current_state_title(request)))
    if context.content_type == 'Poll': #Redirect to polls anchor
        url = request.resource_url(context.__parent__, anchor = context.uid)
    else:
        url = request.resource_url(context)
    return HTTPFound(location = url)
