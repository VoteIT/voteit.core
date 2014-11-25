import unittest

from pyramid import testing
from betahaus.viewcomponent import render_view_action


class MainViewComponentTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_render_flash_messages(self):
        from voteit.core.models.interfaces import IFlashMessages
        self.config.include('pyramid_chameleon')
        self.config.include('voteit.core.models.flash_messages')
        self.config.scan('voteit.core.views.components.main')
        from pyramid.session import UnencryptedCookieSessionFactoryConfig

        def _dummy_request_w_session():
            request = testing.DummyRequest()
            request.session = UnencryptedCookieSessionFactoryConfig('messages')(request)
            return request
        
        context = testing.DummyResource()
        request = _dummy_request_w_session()
        request.session.flash({'msg': 'Hello world', 'type': 'info', 'close_button': True})
        
        class DummyAPI(object):
            def __init__(self, request):
                self.request = request
            @property
            def flash_messages(self):
                return self.request.registry.getAdapter(self.request, IFlashMessages)

        api = DummyAPI(request)
        res = render_view_action(context, request, 'main', 'flash_messages', api = api)
        self.failUnless('Hello world' in res)

    def test_render_poll_state_info(self):
        from voteit.core.models.poll import Poll
        from voteit.core.views.api import APIView
        from voteit.core.testing_helpers import register_workflows
        register_workflows(self.config)
        self.config.include('pyramid_chameleon')
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.include('voteit.core.models.date_time_util')
        self.config.scan('voteit.core.views.components.main')
        #root = active_poll_fixture(self.config)
        #poll = root['meeting']['ai']['poll']
        poll = Poll()
        from voteit.core.models.date_time_util import utcnow
        poll.set_field_value('start_time', utcnow())
        poll.set_field_value('end_time', utcnow())
        request = testing.DummyRequest()
        #obj = self._cut(poll, request)
        api = APIView(poll, request)
        res = render_view_action(poll, request, 'main', 'poll_state_info', api = api)
        #obj.get_poll_state_info(poll)
        self.assertIn('The poll starts', res)
