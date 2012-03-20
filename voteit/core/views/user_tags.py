from pyramid.view import view_config
from pyramid.response import Response
from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPFound

from voteit.core.views.api import APIView
from voteit.core.models.interfaces import IUserTags
from voteit.core.models.interfaces import IBaseContent
from voteit.core.security import VIEW
from voteit.core import VoteITMF as _


class UserTagsView(object):
    """ User tags view handles listing of users who've tagged something.
        It also performs actions to set or unset a tag
        Note that some functionality relies on the request.context attribute.
        That will be the context that the request has.
    """
    
    def __init__(self, request):
        self.api = APIView(request.context, request)
        self.request = request

    @view_config(name="_set_user_tag", context=IBaseContent, permission=VIEW)
    def set_user_tag(self):
        """ View for setting or removing user tags like 'Like' or 'Support'.
            the request.POST object must contain tag and do.
            This view is usually loaded inline, but it's possible to call without js.
        """
        #FIXME: Permission for setting should perhaps be adaptive? Right now all viewers can set.
        #See https://github.com/VoteIT/voteit.core/issues/16
        #FIXME: Use normal colander Schema + CSRF?
        request = self.request
        api = self.api

        tag = request.POST.get('tag')
        do = int(request.POST.get('do')) #0 for remove, 1 for add

        user_tags = request.registry.getAdapter(request.context, IUserTags)

        if do:
            user_tags.add(tag, api.userid)

        if not do:
            user_tags.remove(tag, api.userid)

        if not request.is_xhr:
            return HTTPFound(location=resource_url(request.context, request))
        else:
            brains = api.get_metadata_for_query(uid = request.context.uid)
            assert len(brains) == 1
            brain = brains[0]
            return Response( api.render_single_view_component(brain, request, 'user_tags', tag, api = api) )

    @view_config(name="_tagging_users", context=IBaseContent, renderer='templates/snippets/tagging_users.pt', permission=VIEW)
    def tagging_users(self):
        # FIXME: Each tag type should have it's own view component. That way we can build "private" tags as well.
        context = self.request.context
        api = self.api

        tag = self.request.GET['tag']
        display_name = self.request.GET.get('display_name', _(tag))
        expl_display_name = self.request.GET.get('expl_display_name', _(tag))

        user_tags = self.request.registry.getAdapter(context, IUserTags)
        userids = list(user_tags.userids_for_tag(tag))
        
        response = {}
        response['api'] = api
        response['tag'] = tag
        response['display_name'] = display_name
        response['get_userinfo_url'] = api.get_userinfo_url
        response['userids'] = userids
        response['expl_display_name'] = expl_display_name
        return response
