import colander
import deform
from unittest import TestCase

from pyramid import testing
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.testing_helpers import register_workflows
from voteit.core import security
from voteit.core.views.api import APIView


class ProposalTextValidatorTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.schemas.proposal import ProposalTextValidator
        return ProposalTextValidator

    def test_normal_text(self):
        context = testing.DummyModel()
        api = APIView(context, testing.DummyRequest(),)
        obj = self._cut(context, api, '')
        node = None
        self.assertEqual(obj(node, "Here's some normal text that should pass\nShouldn't it?"), None)

    def test_default_text(self):
        context = testing.DummyModel()
        api = APIView(context, testing.DummyRequest(),)
        obj = self._cut(context, api, '')
        node = None
        from voteit.core.schemas.proposal import deferred_default_proposal_text
        default = api.translate(deferred_default_proposal_text(node, {'context': context}))
        self.assertRaises(colander.Invalid, obj, node, default)
        
    def test_tag_text(self):
        context = testing.DummyModel()
        api = APIView(context, testing.DummyRequest(),)
        tag = 'dummy_tag'
        obj = self._cut(context, api, tag)
        node = None
        from voteit.core.schemas.proposal import deferred_default_proposal_text
        default = api.translate(deferred_default_proposal_text(node, {'context': context, 'tag': tag}))
        self.assertRaises(colander.Invalid, obj, node, default)
        