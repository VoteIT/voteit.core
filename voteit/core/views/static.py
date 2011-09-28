""" Static resources that should be served """
import os
from pkg_resources import resource_filename

from pyramid.response import Response
from pyramid.view import view_config


_voteit_path = resource_filename('voteit.core', '')
_favicon = open(os.path.join(
             _voteit_path, 'static', 'favicon.ico')).read()
_fi_response = Response(content_type='image/x-icon',
                        body=_favicon)


@view_config(name='favicon.ico')
def favicon_view(context, request):
    return _fi_response