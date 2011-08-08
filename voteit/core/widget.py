from deform.widget import RadioChoiceWidget

from pkg_resources import resource_filename
from deform import Form
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__).decode('utf-8'))
search_path = (os.path.join(CURRENT_PATH, 'views/templates/widgets'), resource_filename('deform', 'templates'))
Form.set_zpt_renderer(search_path)

class StarWidget(RadioChoiceWidget):
    #FIXME: the resources for this widget is now hardcoded into main.pt, they should be added through deform resource manager
#    requirements = ( ('jquery.rating', None), )
    template = 'star_choice'
    readonly_template = 'readonly/star_choice'
    
resources = {
    'jquery.rating': {
        None:{
            'js':'scripts/jquery.rating.js',
            'css':'css/jquery.rating.css',
            },
        },
}
