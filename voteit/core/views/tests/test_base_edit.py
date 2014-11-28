import unittest

from pyramid import testing
from pyramid.exceptions import BadCSRFToken
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
import colander

from voteit.core.testing_helpers import bootstrap_and_fixture
from webob.multidict import MultiDict


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    root = bootstrap_and_fixture(config)
    root['m'] = meeting = Meeting()
    return meeting


class BaseFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()
     
    @property
    def _cut(self):
        from voteit.core.views.base_edit import BaseForm
        return BaseForm

    def test_csrf_protection_get(self):
        context = _fixture(self.config)
        request = testing.DummyRequest()
        cls = self._cut
        cls.schema = colander.Schema()
        cls.check_csrf = True
        obj = cls(context, request)
        self.assertIsInstance(obj(), dict)

    def test_csrf_protection_post_no_header(self):
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST')
        cls = self._cut
        cls.schema = colander.Schema()
        cls.check_csrf = True
        obj = cls(context, request)
        self.assertRaises(BadCSRFToken, obj)

    def test_csrf_protection_post_correct_header(self):
        self.config.set_session_factory(testing.DummySession)
        session = testing.DummySession()
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST', headers = {'X-CSRF-Token': session.get_csrf_token()})
        cls = self._cut
        cls.schema = colander.Schema()
        cls.check_csrf = True
        obj = cls(context, request)
        self.assertIsInstance(obj(), dict)

    def test_csrf_protection_disabled(self):
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST')
        cls = self._cut
        cls.schema = colander.Schema()
        cls.check_csrf = False
        obj = cls(context, request)
        self.assertIsInstance(obj(), dict)

    def test_cancel_action(self):
        self.config.include('voteit.core.models.flash_messages')
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST', params = {'cancel': 'Cancel'})
        cls = self._cut
        cls.schema = colander.Schema()
        cls.check_csrf = False
        obj = cls(context, request)
        self.assertIsInstance(obj(), HTTPFound)

    def test_default_fail(self):
        class Schema(colander.Schema):
            title = colander.SchemaNode(colander.String())

        self.config.include('voteit.core.models.flash_messages')
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST', params = {'save': 'Save'})
        cls = self._cut
        cls.schema = Schema()
        cls.check_csrf = False
        cls.save_success = lambda x: x #pyramid_deform expects this
        obj = cls(context, request)
        response = obj()
        self.assertIn('error', response['form'])


class DefaultAddFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()
     
    @property
    def _cut(self):
        from voteit.core.views.base_edit import DefaultAddForm
        return DefaultAddForm

    def test_add_form(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.scan('voteit.core.views.components.tabs_menu')
        context = _fixture(self.config)
        request = testing.DummyRequest(params={'content_type': 'AgendaItem'})
        obj = self._cut(context, request)
        response = obj()
        self.assertIn('form', response)

    def test_add_form_no_permission(self):
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        context = _fixture(self.config)
        request = testing.DummyRequest(params={'content_type': 'AgendaItem'})
        obj = self._cut(context, request)
        self.assertRaises(HTTPForbidden, obj)

    def test_add_ai(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        self.config.scan('voteit.core.models.agenda_item')
        self.config.scan('voteit.core.schemas.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        context = _fixture(self.config)
        request = testing.DummyRequest(params={'content_type': 'AgendaItem'},
                                       post={'add': 'add', 'title': 'Dummy'})
        obj = self._cut(context, request)
        response = obj()
        self.assertEqual(response.location, 'http://example.com/m/dummy/')


class AddMeetingFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.base_edit import AddMeetingForm
        return AddMeetingForm

    def test_add_meeting(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        self.config.scan('voteit.core.models.meeting')
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        context = _fixture(self.config).__parent__
        post = MultiDict([('title', 'Dummy'),
                          ('meeting_mail_name', 'Dummy'),
                          ('meeting_mail_address', 'dummy@site.com'),
                          ('description', u''),
                          ('public_description', u''),
                          ('__start__', 'access_policy:rename'),
                          ('deformField6', 'invite_only'),
                          ('__end__', 'access_policy:rename'),
                          ('add', 'add'),])
        request = testing.DummyRequest(params = {'content_type': 'Meeting'},
                                       method = 'POST',
                                       post = post)
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/dummy/')


class AddPollFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.base_edit import AddPollForm
        return AddPollForm

    def test_add_poll(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.scan('voteit.core.models.poll')
        self.config.scan('voteit.core.schemas.poll')
        self.config.include('voteit.core.plugins.majority_poll')
        self.config.include('voteit.core.models.flash_messages')
        meeting = _fixture(self.config)
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
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location.split('#')[0], 'http://example.com/m/ai/') #A redirect with an anchor



class AddUserFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.base_edit import AddUserForm
        return AddUserForm

    def test_add_user(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        #self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        #self.config.registry.settings['default_locale_name'] = 'sv'
        #self.config.include('voteit.core.models.date_time_util')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.schemas.user')
        #self.config.include('voteit.core.plugins.majority_poll')
        self.config.include('voteit.core.models.flash_messages')
        root = bootstrap_and_fixture(self.config)
        context = root['users']
        postdata = MultiDict([('userid', 'dummy'),
                              ('__start__', 'password:mapping'),
                              ('password', 'secret'),
                              ('password-confirm', 'secret'),
                              ('__end__', 'password:mapping'),
                              ('email', 'john@doe.com'),
                              ('first_name', 'John'),
                              ('add', 'Add')])
        request = testing.DummyRequest(params = {'content_type': 'User'},
                                       post = postdata,
                                       method = 'POST')
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/users/dummy/')
        user = context['dummy']
        self.assertEqual(user.get_field_value('email'), 'john@doe.com')


class DefaultEditFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.base_edit import DefaultEditForm
        return DefaultEditForm

    def test_get_schema(self):
        from voteit.core.schemas.meeting import EditMeetingSchema
        self.config.scan('voteit.core.models.meeting')
        self.config.scan('voteit.core.schemas.meeting')
        context = _fixture(self.config)
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertIsInstance(obj.get_schema(), EditMeetingSchema)

    def test_save_success(self):
        self.config.scan('voteit.core.models.meeting')
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST',
                                       post = {'title': 'Dummy',
                                               'meeting_mail_name': 'Dummy',
                                               'meeting_mail_address': 'dummy@site.com',
                                               'came_from': 'http://example.com/someplace',
                                               'save': 'Save'})
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/someplace')
        self.assertEqual(context.title, 'Dummy')


class DefaultDeleteFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.base_edit import DefaultDeleteForm
        return DefaultDeleteForm

    def test_delete_success(self):
        self.config.include('voteit.core.models.flash_messages')
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST',
                                       post = {'delete': 'Delete'})
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/')
        self.assertNotIn('m', context)


class StateChangeTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.base_edit import state_change
        return state_change

    def test_state_change_not_allowed(self):
        context = _fixture(self.config)
        request = testing.DummyRequest(params = {'state': 'dont_exist'})
        self.assertRaises(HTTPForbidden, self._fut, context, request)

    def test_state_change_allowed(self):
        self.config.include('voteit.core.models.flash_messages')
        context = _fixture(self.config)
        request = testing.DummyRequest(params = {'state': 'ongoing'})
        response = self._fut(context, request)
        self.assertEqual(response.location, 'http://example.com/m/')
        self.assertEqual(context.get_workflow_state(), 'ongoing')
