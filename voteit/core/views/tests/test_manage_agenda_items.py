import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class MeetingViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.manage_agenda_items import ManageAgendaItemsView
        return ManageAgendaItemsView

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        root.users['dummy'] = User()
        return meeting

    def test_order_agenda_items(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.order_agenda_items()
        self.assertIn('title', response)
        
    def test_order_agenda_items_save(self):
        self.config.scan('voteit.core.subscribers.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        context['a1'] = AgendaItem(title = 'Agenda Item 1')
        context['a2'] = AgendaItem(title = 'Agenda Item 2')
        context['a3'] = AgendaItem(title = 'Agenda Item 3')
        request = testing.DummyRequest(post = {'save': 'save', 
                                               'agenda_items': 'a1', 
                                               'agenda_items': 'a2', 
                                               'agenda_items': 'a3'},)
        obj = self._cut(context, request)
        response = obj.order_agenda_items()
        self.assertIn('title', response)
        
    def test_order_agenda_items_cancel(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        request = testing.DummyRequest(post = {'cancel': 'cancel',})
        obj = self._cut(context, request)
        response = obj.order_agenda_items()
        self.assertEqual(response.location, 'http://example.com/m/')
