from deform.widget import RadioChoiceWidget

from voteit.core.fanstaticlib import star_rating


class StarWidget(RadioChoiceWidget):
    """ Star widget for raiting alternatives.
        Use keyword creator_info to pass along creator information.
        See voteit.schulze.models for example code.
    """
    template = 'star_choice'
    readonly_template = 'readonly/star_choice'

    def __init__(self, **kw):
        super(StarWidget, self).__init__(**kw)
        star_rating.need()
