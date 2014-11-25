import unittest

from pyramid import testing
from betahaus.viewcomponent.interfaces import IViewGroup
from betahaus.viewcomponent.models import ViewAction
from betahaus.viewcomponent.models import ViewGroup


class LoginBoxTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.sidebars import login_box
        return login_box

    def test_login_box(self):
        self.config.include('pyramid_chameleon')
        self.config.scan('voteit.core.schemas.user')
        context = testing.DummyModel()
        request = testing.DummyRequest()
        va = ViewAction(object, 'name')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('<span>Login</span>', response)

    def test_login_box_register_page(self):
        self.config.include('pyramid_chameleon')
        self.config.scan('voteit.core.schemas.user')
        context = testing.DummyModel()
        request = testing.DummyRequest(path='/register')
        va = ViewAction(object, 'name')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('', response)

    def test_login_box_login_page(self):
        self.config.include('pyramid_chameleon')
        self.config.scan('voteit.core.schemas.user')
        context = testing.DummyModel()
        request = testing.DummyRequest(path='/login')
        va = ViewAction(object, 'name')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('', response)

    def test_login_already_logged_in(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy('dummy', permissive=True)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        va = ViewAction(object, 'name')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('', response)


class LoginAltTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.sidebars import alternative_login_methods
        return alternative_login_methods

    def _register_dummy_va(self):
        def _dummy_callable(*args, **kw):
            return "Hello world"
        view_group = ViewGroup('login_forms')
        self.config.registry.registerUtility(view_group, IViewGroup, name = 'login_forms')
        view_group.add(ViewAction(_dummy_callable, 'dummy'))

    def test_nothing_to_render(self):
        self.config.scan('voteit.core.schemas.user')
        context = testing.DummyModel()
        request = testing.DummyRequest()
        va = ViewAction(object, 'name')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('', response)

    def test_render_dummy(self):
        self.config.include('pyramid_chameleon')
        self.config.scan('voteit.core.schemas.user')
        self._register_dummy_va()
        context = testing.DummyModel()
        request = testing.DummyRequest()
        va = ViewAction(object, 'name')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('id="login_alt"', response)
        self.assertIn('Hello world', response)



def _api(context=None, request=None):
    from voteit.core.views.api import APIView
    context = context and context or testing.DummyResource()
    request = request and request or testing.DummyRequest()
    return APIView(context, request)
