from pyramid.view import view_config

from voteit.core.views.base_view import BaseView
from voteit.core.models.agenda_item import AgendaItem


class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=AgendaItem, renderer="templates/agenda_item.pt")
    def agenda_item_view(self):
        """ """
        return self.response