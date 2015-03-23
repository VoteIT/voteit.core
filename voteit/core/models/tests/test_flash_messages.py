import unittest

from pyramid import testing
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
import transaction

from voteit.core.models.interfaces import IFlashMessages


class FlashMessagesTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.flash_messages import FlashMessages
        return FlashMessages

    def _dummy_request(self):
        request = testing.DummyRequest()
        request.session = UnencryptedCookieSessionFactoryConfig('messages')(request)
        return request

    def test_verify_class(self):
        self.assertTrue(verifyClass(IFlashMessages, self._cut))

    def test_verify_obj(self):
        #It's okay to adapt none if we don't check the adapted context in __init__
        self.assertTrue(verifyObject(IFlashMessages, self._cut(None)))

    def test_add(self):
        request = self._dummy_request()
        obj = self._cut(request)
        transaction.begin()
        obj.add("Message")
        transaction.commit()
        res = tuple(request.session.pop_flash())
        self.assertEqual(len(res), 1)

    def test_get_messages(self):
        request = self._dummy_request()
        request.session.flash({'msg': 'Hello world'})
        obj = self._cut(request)
        res = [x for x in obj.get_messages()]
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['msg'], 'Hello world')

    def test_register_adapter(self):
        self.config.include('voteit.core.models.flash_messages')
        request = testing.DummyRequest()
        self.assertTrue(self.config.registry.queryAdapter(request, IFlashMessages))
