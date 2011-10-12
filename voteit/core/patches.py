""" Contains things that should be loaded on startup.
    This file should be removed as soon as we can register things in a smarter way,
    or persuade the deform gang to include hooks for this kind of stuff :)
"""

from os.path import join
from pkg_resources import resource_filename

from deform import Form
from deform.widget import RadioChoiceWidget

from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request


def translator(term):
    return get_localizer(get_current_request()).translate(term)


CURRENT_PATH = resource_filename('voteit.core', '')
WIDGET_PATH = join(CURRENT_PATH, 'views', 'templates', 'widgets')
search_path = (WIDGET_PATH,
               resource_filename('deform', 'templates'))

Form.set_zpt_renderer(search_path, translator=translator)

#Patch radio choice widget to use a sane readonly template
RadioChoiceWidget.readonly_template = join(WIDGET_PATH, 'readonly', 'radio_choice')