import unittest
from datetime import timedelta
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyObject
from pyramid_mailer import get_mailer


class UserTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.user import User
        return User()

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IUser
        obj = self._make_obj()
        self.assertTrue(verifyObject(IUser, obj))

    def test_new_request_password_token(self):
        obj = self._make_obj()
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        
        obj.new_request_password_token(request)
        
        self.failUnless(obj.__token__())
    
    def test_new_request_password_token_mailed(self):
        obj = self._make_obj()
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        
        obj.new_request_password_token(request)

        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        
        msg = mailer.outbox[0]
        
        self.failUnless(obj.__token__() in msg.body)

#FIXME: Should be done in the form context
#    def test_validate_password_token(self):
        

class RequestPasswordTokenTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.models.user import RequestPasswordToken
        return RequestPasswordToken()

    def test_initial_values(self):
        obj = self._make_obj()
        self.assertEqual(obj.created + timedelta(days=3), obj.expires)

    def test_call_returns_token(self):
        obj = self._make_obj()
        self.assertEqual(obj(), obj.token)
        self.assertEqual(len(obj()), 30)
    
    def test_validate_works(self):
        obj = self._make_obj()
        obj.token = 'dummy'
        obj.validate('dummy')
    
    def test_validate_expired(self):
        obj = self._make_obj()
        obj.token = 'dummy'
        obj.expires = datetime.now() - timedelta(days=1)
        self.assertRaises(ValueError, obj.validate, 'dummy')

    def test_validate_wrong_token(self):
        obj = self._make_obj()
        obj.token = 'dummy'
        self.assertRaises(ValueError, obj.validate, 'wrong')
