import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject


class TZDateTimeTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.schemas.tzdatetime import TZDateTime
        return TZDateTime

    #FIXME: When TZDateTime issues are fixed, write tests