import unittest

from pyramid import testing


class MainViewComponentTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_render_flash_messages(self):
        from voteit.core.models.interfaces import IFlashMessages
        from voteit.core.views.components.main import render_flash_messages as fut
        self.config.include('voteit.core.models.flash_messages')
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
        res = fut(context, request, api = api)
        self.failUnless('Hello world' in res)
