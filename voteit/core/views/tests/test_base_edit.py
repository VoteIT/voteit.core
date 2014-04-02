import unittest

from pyramid import testing
from pyramid.exceptions import Forbidden
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture


class DefaultEditTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.base_edit import DefaultEdit
        return DefaultEdit
    
    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        return meeting
    
    def test_add_form(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.scan('voteit.core.views.components.tabs_menu')
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'AgendaItem'})
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('form', response)
        
    def test_add_form_no_permission(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'AgendaItem'})
        obj = self._cut(context, request)
        self.assertRaises(Forbidden, obj.add_form)
        
    def test_add_form_cancel(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        self.config.scan('voteit.core.views.components.tabs_menu')
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'AgendaItem'}, post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertEqual(response.location, 'http://example.com/m/')
    
    def test_add_form_validation_error(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.scan('voteit.core.views.components.tabs_menu')
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'AgendaItem'}, post={'add': 'add', 'title': ''})
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('form', response)
        
    def test_add_form_add_poll(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.scan('voteit.core.models.poll')
        self.config.scan('voteit.core.schemas.poll')
        self.config.include('voteit.core.plugins.majority_poll')
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest(params={'content_type': 'Poll'}, post=MultiDict([('add', 'add'), 
                                                                                       ('title', 'Dummy poll'),
                                                                                       ('description', 'description'),
                                                                                       ('poll_plugin', 'majority_poll'),
                                                                                       ('__start__', 'proposals:sequence'),
                                                                                       ('__end__', 'proposals:sequence'),
                                                                                       ('reject_proposal_title', 'Reject all proposals'),
                                                                                       ('start_time', '2012-05-15 12:00'),
                                                                                       ('end_time', '2012-05-16 12:00')]))
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertEqual(response.location.split('#')[0], 'http://example.com/m/ai/') #A redirect with an anchor

    def test_edit_form(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.edit_form()
        self.assertIn('form', response)
        
    def test_edit_form_cancel(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.edit_form()
        self.assertEqual(response.location, 'http://example.com/m/ai/')
    
    def test_edit_form_validation_error(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest(post={'update': 'update', 'title': ''})
        obj = self._cut(context, request)
        response = obj.edit_form()
        self.assertIn('form', response)
        
    def test_edit_form_update(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem(title='Dummy AI updated', description='Dummy description')
        post_vars = {'update': 'update',
                     'title': 'Dummy AI',
                     'description': 'Dummy description',
                     'csrf_token': '0123456789012345678901234567890123456789'}
        request = testing.DummyRequest(post=post_vars)
        obj = self._cut(context, request)
        response = obj.edit_form()
        self.assertEqual(response.location, 'http://example.com/m/ai/')
        
    def test_edit_form_same(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem(title='Dummy AI', description='Dummy description')
        post_vars = {'update': 'update',
                     'title': 'Dummy AI',
                     'description': 'Dummy description',
                     'csrf_token': '0123456789012345678901234567890123456789'}
        request = testing.DummyRequest(post=post_vars)
        obj = self._cut(context, request)
        response = obj.edit_form()
        self.assertEqual(response.location, 'http://example.com/m/ai/')

    def test_delete_form(self):
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.delete_form()
        self.assertIn('form', response)
        
    def test_delete_form_proposal(self):
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        meeting['ai'] = ai = AgendaItem()
        ai['p'] = context = Proposal()
        request = testing.DummyRequest()
        context.set_workflow_state(request, 'voting')
        obj = self._cut(context, request)
        response = obj.delete_form()
        self.assertIn('form', response)
        
    def test_delete_form_cancel(self):
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.delete_form()
        self.assertEqual(response.location, 'http://example.com/m/ai/')
 
    def test_delete_form_delete(self):
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest(post={'delete': 'delete'})
        obj = self._cut(context, request)
        response = obj.delete_form()
        self.assertNotIn('ai', meeting)
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_delete_form_delete_forbidden(self):
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        context = meeting.__parent__ 
        request = testing.DummyRequest(post={'delete': 'delete'})
        obj = self._cut(context, request)
        self.assertRaises(Exception, obj.delete_form)
       
    def test_state_change(self):
        context = self._fixture()
        request = testing.DummyRequest(params={'state': 'ongoing'})
        obj = self._cut(context, request)
        response = obj.state_change()
        self.assertEqual(response.location, 'http://example.com/m/')