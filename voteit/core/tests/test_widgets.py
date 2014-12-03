import unittest

import colander
import deform
from pyramid import testing
from fanstatic import get_needed
from fanstatic import init_needed
from fanstatic import NeededResources


class StarWidgetTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.widgets import StarWidget
        return StarWidget

    def test_start_raiting_included(self):
        from voteit.core.fanstaticlib import _star_rating_css
        init_needed()
        obj = self._cut()
        needed = get_needed().resources()
        self.assertIn(_star_rating_css, needed)
