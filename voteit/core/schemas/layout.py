import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core import VoteITMF as _


NA_CHOICE = (('', _(u"None available")))

def _get_choices(request, group_name):
    util = request.registry.queryUtility(IViewGroup, name = group_name)
    if util is None:
        return NA_CHOICE
    choices = []
    choices.append(('', _(u"<Nothing>")))
    for (name, va) in util.items():
        title = va.title and va.title or name
        item = (name, title)
        choices.append(item)
    return choices

@colander.deferred
def deferred_meeting_layout_widget(node, kw):
    request = kw['request']
    choices = _get_choices(request, 'meeting_widgets')
    return deform.widget.RadioChoiceWidget(values=choices)


@colander.deferred
def deferred_ai_layout_widget(node, kw):
    request = kw['request']
    choices = _get_choices(request, 'agenda_item_widgets')
    return deform.widget.RadioChoiceWidget(values=choices)


@schema_factory('LayoutSchema')
class LayoutSchema(colander.Schema):
    meeting_left_widget = colander.SchemaNode(colander.String(),
                                              widget = deferred_meeting_layout_widget,
                                              default = 'description_richtext',)
    meeting_right_widget = colander.SchemaNode(colander.String(),
                                               widget = deferred_meeting_layout_widget,
                                               missing = colander.null,)
    ai_left_widget = colander.SchemaNode(colander.String(),
                                         widget = deferred_ai_layout_widget,
                                         missing = colander.null,)
    ai_right_widget = colander.SchemaNode(colander.String(),
                                          widget = deferred_ai_layout_widget,
                                          missing = colander.null,)
