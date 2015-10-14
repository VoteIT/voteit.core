import unittest

from pyramid import testing


class TestingHelperTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _module(self):
        from voteit.core import testing_helpers
        return testing_helpers

    def test_dummy_zodb_root(self):
        root = self._module.dummy_zodb_root(self.config)
        self.failUnless('users' in root)
