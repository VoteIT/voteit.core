from pyramid.traversal import find_interface
from pyramid.renderers import render
from repoze.workflow import get_workflow

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import MODERATE_MEETING


def creators_info(request, creators, portrait = True):
    users = []
    for userid in creators:
        user = request.root['users'].get(userid, None)
        if user:
            users.append(user)
    return render('voteit.core:templates/snippets/creators_info.pt', {'users': users, 'portrait': portrait}, request = request)

def get_meeting(request):
    return find_interface(request.context, IMeeting)

def get_userinfo_url(request, userid):
    return request.resource_url(request.meeting, '__userinfo__', userid)

def is_moderator(request):
    return request.has_permission(MODERATE_MEETING, request.meeting)

def get_wf_state_titles(request, iface, type_name):
    wf = get_workflow(iface, type_name)
    results = {}
    for sinfo in wf.state_info(None, request):
        results[sinfo['name']] = request.localizer.translate(sinfo['title'], domain = 'voteit.core')
    return results

def includeme(config):
    config.include('.agenda_item')
    config.include('.cogwheel')
    config.scan(__name__)

    #Hook creators info
    config.add_request_method(callable = creators_info, name = 'creators_info')
    #Hook meeting
    config.add_request_method(callable = get_meeting, name = 'meeting', reify = True)
    #Userinfo URL
    config.add_request_method(callable = get_userinfo_url, name = 'get_userinfo_url')
    #Is moderator
    config.add_request_method(callable = is_moderator, name = 'is_moderator', reify = True)
    #State titles
    config.add_request_method(callable = get_wf_state_titles, name = 'get_wf_state_titles')
