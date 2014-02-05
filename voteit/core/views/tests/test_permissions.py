import unittest

from pyramid import testing
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture


class PermissionsViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.permissions import PermissionsView
        return PermissionsView
    
    def _fixture(self):
        self.config.scan('voteit.core.schemas.permissions')
        self.config.scan('voteit.core.views.components.tabs_menu')
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        return root
    
    def test_group_form_root(self):
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.group_form()
        self.assertIn('form', response)
        
    def test_group_form_meeting(self):
        root = self._fixture()
        from voteit.core.models.meeting import Meeting
        root['m'] = context = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.group_form()
        self.assertIn('form', response)
        
    def test_group_form_root_cancel(self):
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.group_form()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_group_form_meeting_cancel(self):
        root = self._fixture()
        from voteit.core.models.meeting import Meeting
        root['m'] = context = Meeting()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.group_form()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_group_form_root_save(self):
        context = self._fixture()
        request = testing.DummyRequest(post = MultiDict([('__start__', 'userids_and_groups:sequence'),
                                                           ('__start__', 'userid_and_groups:mapping'),
                                                           ('userid', 'admin'), 
                                                           ('__start__', 'groups:sequence'),
                                                           ('checkbox', 'role:Admin'), 
                                                           ('__end__', 'groups:sequence'),
                                                           ('__end__', 'userid_and_groups:mapping'),
                                                           ('__end__', 'userids_and_groups:sequence'),
                                                           ('csrf_token', '0123456789012345678901234567890123456789'),
                                                           ('save', 'save')]))
        obj = self._cut(context, request)
        response = obj.group_form()
        self.assertEqual(response.location, 'http://example.com/')

    def test_group_form_root_validation_error(self):
        context = self._fixture()
        request = testing.DummyRequest(post = MultiDict([('__start__', 'userids_and_groups:sequence'),
                                                           ('__start__', 'userid_and_groups:mapping'),
                                                           ('userid', ''), 
                                                           ('__start__', 'groups:sequence'),
                                                           ('checkbox', 'role:Admin'), 
                                                           ('__end__', 'groups:sequence'),
                                                           ('__end__', 'userid_and_groups:mapping'),
                                                           ('__end__', 'userids_and_groups:sequence'),
                                                           ('save', 'save')]))
        obj = self._cut(context, request)
        response = obj.group_form()
        self.assertIn('form', response)
        
    def test_add_permission_root(self):
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.add_permission()
        self.assertIn('form', response)

    def test_add_permission_meeting(self):
        root = self._fixture()
        from voteit.core.models.meeting import Meeting
        root['m'] = context = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.add_permission()
        self.assertIn('form', response)
        
    def test_add_permission_root_cancel(self):
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.add_permission()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_add_permission_meeting_cancel(self):
        root = self._fixture()
        from voteit.core.models.meeting import Meeting
        root['m'] = context = Meeting()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.add_permission()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_add_permission_root_save(self):
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        request = testing.DummyRequest(post = MultiDict([('userid', 'admin'), 
                                                         ('__start__', 'groups:sequence'),  
                                                         ('checkbox', 'role:Admin'), 
                                                         ('__end__', 'groups:sequence'),
                                                         ('csrf_token', '0123456789012345678901234567890123456789'),
                                                         ('add', 'add')]))
        obj = self._cut(context, request)
        response = obj.add_permission()
        self.assertEqual(response.location, 'http://example.com/')

    def test_add_permission_root_validation_error(self):
        context = self._fixture()
        request = testing.DummyRequest(post = MultiDict([('userid', ''), 
                                                         ('__start__', 'groups:sequence'), 
                                                         ('checkbox', 'role:Moderator'), 
                                                         ('checkbox', 'role:Viewer'), 
                                                         ('__end__', 'groups:sequence'), 
                                                         ('save', 'save')]))
        obj = self._cut(context, request)
        response = obj.add_permission()
        self.assertIn('form', response)
        
    def test_add_permission_meeting_validation_error(self):
        root = self._fixture()
        from voteit.core.models.meeting import Meeting
        root['m'] = context = Meeting()
        request = testing.DummyRequest(post = MultiDict([('userid', ''), 
                                                         ('__start__', 'groups:sequence'), 
                                                         ('checkbox', 'role:Moderator'), 
                                                         ('checkbox', 'role:Viewer'), 
                                                         ('__end__', 'groups:sequence'), 
                                                         ('save', 'save')]))
        obj = self._cut(context, request)
        response = obj.add_permission()
        self.assertIn('form', response)