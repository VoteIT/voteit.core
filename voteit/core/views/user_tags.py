from pyramid.view import view_config
from pyramid.security import authenticated_userid
from pyramid.i18n import get_localizer
from pyramid.response import Response
from pyramid.url import resource_url
from pyramid.renderers import render

from voteit.core.models.interfaces import IUserTags
from voteit.core.models.interfaces import IBaseContent
from voteit.core import VoteITMF as _


class UserTagsView(object):
    """ User tags view for rendering controls and displaying button.
        Note the request.context attribute in set_user_tag
        and that context is passed along to get_user_tag.
        It's important that the adapter is rechecked for each context,
        otherwise it will retrieve data from the wrong context.
    """
    
    def __init__(self, request):
        self.userid = authenticated_userid(request)
        if not self.userid:
            raise Forbidden("You're not allowed to access this view.")
        
        self.request = request
        self.localizer = get_localizer(request)

    @view_config(name="_set_user_tag", context=IBaseContent)
    def set_user_tag(self):
        """ View for setting or removing user tags like 'Like' or 'Support'.
            the request.POST object must contain tag and do.
            This view is usually loaded inline, but it's possible to call without js.
        """
        #FIXME: Use normal colander Schema + CSRF?
        request = self.request
        tag = request.POST.get('tag')
        do = int(request.POST.get('do')) #0 for remove, 1 for add

        user_tags = request.registry.getAdapter(request.context, IUserTags)

        if do:
            user_tags.add(tag, self.userid)
    
        if not do:
            user_tags.remove(tag, self.userid)
            
        display_name = request.POST.get('display_name')
        expl_display_name = request.POST.get('expl_display_name')
    
        if not request.is_xhr:
            return HTTPFound(location=resource_url(self.context, request))
        else:
            
            return Response(self.get_user_tag(request.context, tag, display_name, expl_display_name))

    def get_user_tag(self, context, tag, display_name, expl_display_name):
        user_tags = self.request.registry.getAdapter(context, IUserTags)
        userids = list(user_tags.userids_for_tag(tag))
        
        response = {}
        response['context_id'] = context.uid
        response['toggle_url'] = "%s_set_user_tag" % resource_url(context, self.request)
        response['tag'] = tag
        response['display_name'] = display_name
        
        if self.userid and self.userid in userids:
            #Note: It's not possible to have nested translation strings. Hence this
            response['button_label'] = _(u"Remove ${display_name}",
                                         mapping={'display_name':self.localizer.translate(display_name)})
            response['selected'] = True
            response['do'] = "0"
            userids.remove(self.userid)
        else:
            response['button_label'] = display_name
            response['selected'] = False
            response['do'] = "1"
        
        response['has_entries'] = bool(response['selected'] or userids)
        response['userids'] = userids
        #This label is for after the listing, could be "4 people like this"
        response['expl_display_name'] = expl_display_name
        
        return render('templates/snippets/user_tag.pt', response, request=self.request)
        
