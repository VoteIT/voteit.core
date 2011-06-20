import unittest
from pyramid import testing
from pyramid.interfaces import IRequest
from zope.interface.verify import verifyObject

from voteit.core.app import register_request_factory



class VoteITRequestMixinTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        register_request_factory(self.config)

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.testing import DummyRequestWithVoteIT
        return DummyRequestWithVoteIT()
    
    def test_verify_interface(self):
        obj = self._make_obj()
        
        self.assertTrue(verifyObject(IRequest, obj))
