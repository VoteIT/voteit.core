from betahaus.viewcomponent import view_action

@view_action('main', 'logo_tag')
def logo_image_tag(context, request, *args, **kwargs):
    url = "%s/static/images/logo.png" % request.application_url
    return '<img src="%(url)s" height="%(h)s" width="%(w)s" id="logo" />' % {'url':url, 'h':31, 'w':85}
