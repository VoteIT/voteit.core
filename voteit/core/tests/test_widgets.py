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


class RecaptchaWidgetTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest(remote_addr = '127.0.0.1')
        self.config = testing.setUp(request = request)
        self.config.include('voteit.core.deform_bindings')

    def tearDown(self):
        self.config.include('voteit.core.deform_bindings.reset_deform')
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.widgets import RecaptchaWidget
        return RecaptchaWidget

    def _dummy_field(self):
        class DummySchema(colander.Schema):
            this_field = colander.SchemaNode(colander.String(),
                                             widget = self._cut())
        form = deform.Form(DummySchema())
        return form['this_field']

    def test_serialize(self):
        obj = self._cut()
        field = self._dummy_field()
        self.assertIn('http://www.google.com/recaptcha', obj.serialize(field, ''))

#We can't test this since it requires active network connection and a working API key :/
#    def test_deserialize(self):
#        obj = self._cut(PUBKEY, PRIVKEY)
#        field = self._dummy_field()
#        pstruct = {u'recaptcha_challenge_field': u'dummy', u'recaptcha_response_field': u'sdfs'}
#        try:
#            res = obj.deserialize(field, pstruct)
#        except colander.Invalid, e:
#            self.assertEqual(e.msg, 'invalid-request-cookie')
