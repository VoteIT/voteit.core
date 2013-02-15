from betahaus.viewcomponent import view_action


@view_action('head', 'title')
def page_title(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        if context == api.meeting:
            title = api.meeting.title
        else:
            title = u"%s | %s" % (context.title, api.meeting.title)
    else:
        if context == api.root:
            title = api.root.get_field_value('site_title', u"VoteIT")
        else:
            title = u"%s | %s" % (context.title, api.root.get_field_value('site_title', u"VoteIT"))
    return u"""<title>%s</title>""" % title
