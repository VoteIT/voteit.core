from betahaus.viewcomponent import view_action


@view_action('main', 'creators_info')
def creators_info(context, request, va, **kw):
    api = kw['api']
    creators = kw['creators']
    portrait = kw['portrait']
    if not creators:
        return ''
    output = '<span class="creators">'
    for userid in kw['creators']:
        user = api.get_user(userid)
        if user:
            output += """<a href="%(userinfo_url)s" class="inlineinfo">%(portrait_tag)s %(usertitle)s (%(userid)s)</a>"""\
                % {'userinfo_url': api.get_userinfo_url(userid),
                   'portrait_tag': portrait and user.get_image_tag(request = request) or '',
                   'usertitle': user.title,
                   'userid':userid,}
        else:
            output += "(%s)" % userid
    output += '</span>'
    return output
