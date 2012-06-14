from pyramid.response import Response
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid.security import NO_PERMISSION_REQUIRED

from voteit.core.models.interfaces import IJSUtil


@view_config(name = 'translations.js', permission = NO_PERMISSION_REQUIRED)
def js_translations_view(context, request):
    """ Include translations needed for javascripts.
        This should be processed before running other javascripts,
        otherwise they won't be able to access translations.
    """
    util = request.registry.getUtility(IJSUtil)
    res = {'translations': util.get_translations()}
    renderer = render("templates/js_translations.pt", res, request = request)
    return Response(renderer, content_type='text/javascript') 
