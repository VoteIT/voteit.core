# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.interfaces import IRoot
from arche.views.base import BaseView
from pyramid.view import view_config


@view_config(context=IRoot,
             name='manifest.json',
             renderer='json')
class ManifestJson(BaseView):
    """ Manifest file """
    defaults = {
        'short_name': 'VoteIT',
        'name': 'VoteIT',
        'start_url': '/',
        'background_color': '#0a243d',
        'theme_color': '#0a243d',
        'display': 'standalone',
        'lang': 'en',
        'icons': (
            {
                'src': '/voteit_core_static/images/voteit-logo-manifest-48.png',
                'type': 'image/png',
                'sizes': '48x48',
            },
            {
                'src': '/voteit_core_static/images/voteit-logo-manifest-128.png',
                'type': 'image/png',
                'sizes': '128x128',
            },
            {
                'src': '/voteit_core_static/images/voteit-logo-manifest-192.png',
                'type': 'image/png',
                'sizes': '192x192',
            },
            {
                'src': '/voteit_core_static/images/voteit-logo-manifest-256.png',
                'type': 'image/png',
                'sizes': '256x256',
            },
        )
    }

    def __call__(self):
        manifest = {}
        for key, value in self.defaults.items():
            manifest[key] = self.request.registry.settings.get('manifest.{}'.format(key), value)
        return manifest
