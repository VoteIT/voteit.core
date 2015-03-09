from pyramid.traversal import find_interface
from pyramid.renderers import render

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import MODERATE_MEETING


def creators_info(request, creators, portrait = True):
    users = []
    for userid in creators:
        user = request.root['users'].get(userid, None)
        if user:
            users.append(user)
    return render('voteit.core:templates/snippets/creators_info.pt', {'users': users, 'portrait': portrait}, request = request)
    
#     return "".join(request.get_userinfo_tag(userid) for userid in creators)
#     out = ""
#     for userid in creators:
#         user = request.root['users'].get(userid, None)
#         if user:
#             users.append(user)
#         
#     output = '<span class="creators">'
#     for userid in creators:
#         user = request.root['users'].get(userid, None)
#         if user:
#             output += """<a href="%(userinfo_url)s" class="inlineinfo">%(portrait_tag)s %(usertitle)s (%(userid)s)</a>"""\
#                 % {'userinfo_url': request.get_userinfo_url(userid),
#                    'portrait_tag': portrait and user.get_image_tag(request = request) or '',
#                    'usertitle': user.title,
#                    'userid':userid,}
#         else:
#             output += "(%s)" % userid
#     output += '</span>'
#     return output

def get_meeting(request):
    return find_interface(request.context, IMeeting)

def get_userinfo_url(request, userid):
    return request.resource_url(request.meeting, '__userinfo__', userid)

# def get_userinfo_tag(request, userid):
#     return """
#     <a class="btn btn-default userinfo">%s</a>
#     """ % userid

def is_moderator(request):
    return request.has_permission(MODERATE_MEETING, request.meeting)

def includeme(config):
    config.include('.agenda_item')
    config.include('.cogwheel')
    config.scan(__name__)

    #Hook creators info
    config.add_request_method(callable = creators_info, name = 'creators_info')
    #Hook meeting
    config.add_request_method(callable = get_meeting, name = 'meeting', reify = True)
    #Userinfo URL
    #config.add_request_method(callable = get_userinfo_tag, name = 'get_userinfo_tag')
    config.add_request_method(callable = get_userinfo_url, name = 'get_userinfo_url')
    #Is moderator
    config.add_request_method(callable = is_moderator, name = 'is_moderator', reify = True)