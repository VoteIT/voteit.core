from deform import Form
from pyramid.view import view_config
from pyramid.response import Response
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.fanstaticlib import voteit_participants


class ParticipantsView(BaseView):

    @view_config(name="participants", context=IMeeting, renderer="templates/participants.pt", permission=security.VIEW)
    def participants_view(self):
        """ List all participants in this meeting, and their permissions. """
        #Viewer role isn't needed, since only users who can view will be listed here.
        self.response['role_viewer'] = security.ROLE_VIEWER
        self.response['role_moderator'] = security.ROLE_MODERATOR
        self.response['role_discuss'] = security.ROLE_DISCUSS
        self.response['role_propose'] = security.ROLE_PROPOSE
        self.response['role_voter'] = security.ROLE_VOTER
        self.response['role_admin'] = security.ROLE_ADMIN
        return self.response

    @view_config(name="_participants_set_groups", context=IMeeting, xhr = True, permission = security.MANAGE_GROUPS)
    def ajax_set_groups(self):
        schema = createSchema('PermissionsSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
        form = Form(schema, buttons=('save', 'cancel'))
        controls = self.request.POST.items()
        appstruct = form.validate(controls)
        #FIXME: Handle error some way, and return a proper response
        self.context.set_security(appstruct['userids_and_groups'])
        return Response() # i.e. 200 ok

    @view_config(name = "_participants_data.json", context = IMeeting,
                 renderer = "json", permission=security.VIEW, xhr = True)
    def participants_json_data(self):
        """ Return a json object with participant data.
            Will return json with this structure:
            
            .. code-block :: py
            
                {'userid':{'first_name': '<name>',
                           'last_name': '<name>',
                           'email': '<email>',
                           'extras: {'extra_data': '<extra_data>',},
                           'role_discuss': '<bool>', #<etc...>,
                          }
        """
        users = self.api.root.users
        results = {}
        #Find the users
        for userid in security.find_authorized_userids(self.context, (security.VIEW,)):
            user = users.get(userid, None)
            if user:
                results[userid] = dict(
                    first_name = user.get_field_value('first_name', u""),
                    last_name = user.get_field_value('last_name', u""),
                    email = user.get_field_value('email', u""),
                    #Make sure context is meeting here!
                    roles = self.context.get_groups(userid)
                )
        return results
