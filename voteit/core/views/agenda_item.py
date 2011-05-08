from pyramid.view import view_config

from voteit.core.views.base_view import BaseView
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.security import VIEW

class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=AgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ """
        return self.response