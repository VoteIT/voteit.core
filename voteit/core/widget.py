from deform.widget import RadioChoiceWidget


class StarWidget(RadioChoiceWidget):
    #FIXME: the resources for this widget is now hardcoded into main.pt, they should be added through deform resource manager
    #requirements = ( ('jquery.rating', None), )
    template = 'star_choice'
    readonly_template = 'readonly/star_choice'
