from pyramid.traversal import find_interface

from voteit.core.models.interfaces import IMeeting


def creators_info(request, creators, portrait = True):
    output = '<span class="creators">'
    for userid in creators:
        user = request.root['users'].get(userid, None)
        if user:
            output += """<a href="%(userinfo_url)s" class="inlineinfo">%(portrait_tag)s %(usertitle)s (%(userid)s)</a>"""\
                % {'userinfo_url': request.get_userinfo_url(userid),
                   'portrait_tag': portrait and user.get_image_tag(request = request) or '',
                   'usertitle': user.title,
                   'userid':userid,}
        else:
            output += "(%s)" % userid
    output += '</span>'
    return output

def get_meeting(request):
    return find_interface(request.context, IMeeting)

def get_userinfo_url(request, userid):
    return request.resource_url(request.meeting, '_userinfo', query = {'userid': userid})

def includeme(config):
    config.include('.portlets')
    config.include('.agenda_item')
    config.scan(__name__)

    #Hook creators info
    config.add_request_method(callable = creators_info, name = 'creators_info')
    #Hook meeting
    config.add_request_method(callable = get_meeting, name = 'meeting', reify = True)
    #Userinfo URL
    config.add_request_method(callable = get_userinfo_url, name = 'get_userinfo_url')
