from arche.populators import Populator

from voteit.core import _
from voteit.core.models.arche_compat import createContent


class VoteITPopulator(Populator):
    name = 'voteit'
    title = _("VoteIT")
    description = _("Create a VoteIT instance")

    def populate(self, **kw):
        self.context.footer = """
            <a href="http://www.voteit.se">www.voteit.se</a> &mdash; 
            <a href="http://manual.voteit.se">User and developer manual</a> &mdash;
            <a href="https://github.com/VoteIT">Source code and bugtracker</a>"""
        #Add users folder
        self.context['agenda_templates'] = createContent('AgendaTemplates', title = _(u"Agenda templates"), creators = ['admin'])

def includeme(config):
    config.add_populator(VoteITPopulator)
