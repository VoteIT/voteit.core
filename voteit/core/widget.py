import os

from deform.widget import RadioChoiceWidget
from deform.widget import default_resource_registry
from pkg_resources import resource_filename
from deform import Form

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__).decode('utf-8'))
search_path = (os.path.join(CURRENT_PATH, 'views/templates/widgets'), resource_filename('deform', 'templates'))
Form.set_zpt_renderer(search_path)

class StarWidget(RadioChoiceWidget):
    #FIXME: the resources for this widget is now hardcoded into main.pt, they should be added through deform resource manager
    #requirements = ( ('jquery.rating', None), )
    template = 'star_choice'
    readonly_template = 'readonly/star_choice'
    
#default_resource_registry.set_js_resources('jquery.rating', None, 'scripts/jquery.rating.js')
#default_resource_registry.set_css_resources('jquery.rating', None, 'css/jquery.rating.css')
