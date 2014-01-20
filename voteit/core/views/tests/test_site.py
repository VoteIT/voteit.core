import unittest

from pyramid import testing
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture


class SiteFormViewTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.site import SiteFormView
        return SiteFormView
#FIXME: Form tests
