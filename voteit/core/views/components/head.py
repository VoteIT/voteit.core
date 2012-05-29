from betahaus.viewcomponent import view_action


@view_action('head', 'title')
def page_title(context, request, va, **kw):
    #FIXME: Proper title based on page name etc? Remember that returing a string won't render translations
    return """<title>VoteIT</title>"""
