from pyramid.view import view_config
from pyramid.response import Response
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core.security import find_authorized_userids
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core.security import EDIT
from voteit.core.security import VIEW
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_delete
from voteit.core.views.base_view import BaseView
from voteit.core.views.base_edit import BaseEdit


DEFAULT_TEMPLATE = "templates/base_edit.pt"


class UsersFormView(BaseEdit):
    """ View class for adding, editing or deleting users.
        It also handles users own login and registration.
    """

    @view_config(context=IUsers, name="add", renderer=DEFAULT_TEMPLATE)
    def add_form(self):
        post = self.request.POST
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)

        schema = createSchema('AddUserSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #Userid and name should be consistent
            name = appstruct['userid']
            del appstruct['userid']
            
            #creators takes care of setting the role owner as well as adding it to creators attr.
            obj = createContent('User', creators=[name], **appstruct)
            self.context[name] = obj
            self.api.flash_messages.add(_(u"Successfully added"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)

        #No action - Render add form
        msg = _(u"Add new user")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    @view_config(context=IUser, renderer='templates/user.pt', permission=VIEW)
    def view_user(self):
        return self.response

    @view_config(context=IUser, name="manage_connections", renderer='templates/base_edit.pt', permission=EDIT)
    def view_edit_manage_connected_profiles(self):
        schema = createSchema('ManageConnectedProfilesSchema').bind(context=self.context, request=self.request)
        form = Form(schema, buttons=(button_delete, button_cancel))
        self.api.register_form_resources(form)
    
        #Handle submitted information
        if 'delete' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            domains = appstruct['auth_domains']
            if domains:
                for domain in domains:
                    del self.context.auth_domains[domain]
                msg = _(u"Removing information for: ${domains}",
                        mapping = {'domains': ", ".join(domains)})
                self.api.flash_messages.add(msg)
            else:
                self.api.flash_messages.add(_(u"Nothing updated"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)
        if 'cancel' in self.request.POST:
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)
        #Render form
        self.response['form'] = form.render()
        return self.response


class UsersView(BaseView):
    """ Any regular view action without forms. """

    @view_config(context=IUsers, renderer='templates/list_users.pt', permission=VIEW)
    def list_users(self):
        self.response['users'] = self.context.get_content(content_type = 'User', sort_on = 'userid')
        return self.response

    @view_config(context=IMeeting, name="_userinfo", permission=VIEW, xhr=True)
    def user_info_ajax_wrapper(self):
        return Response(self.user_info())

    @view_config(context=IMeeting, name="_userinfo", permission=VIEW, xhr=False, renderer="templates/simple_view.pt")
    def user_info_fallback(self):
        self.response['content'] = self.user_info()
        return self.response

    def user_info(self):
        """ Special view to allow other meeting participants to see information about a user
            who's in the same meeting as them.
            Normally called via AJAX and included in a popup or similar, but also a part of the
            users profile page.
            
            Note that a user might have participated within a meeting, and after that lost their
            permission. This view has to at least display the username of that person.
        """
        info_userid = self.request.GET['userid']
        if not info_userid in find_authorized_userids(self.context, (VIEW,)):
            msg = _(u"userid_not_registered_within_meeting_error",
                    default = u"Couldn't find any user with userid '${info_userid}' within this meeting.",
                    mapping = {'info_userid': info_userid})
            return self.api.translate(msg)
        user = self.api.get_user(info_userid)
        return self.api.render_view_group(user, self.request, 'user_info', api = self.api)
