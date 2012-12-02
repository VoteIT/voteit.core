import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class NavigationSectionHeaderTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.navigation import navigation_section_header
        return navigation_section_header


class NavigationSectionTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.navigation import navigation_sections
        return navigation_sections

    def test_navigation_section_root(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = bootstrap_and_fixture(self.config)
        request = testing.DummyRequest()
        va = _va(title='Upcoming', state='upcoming')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('Upcoming', response)
        
    def test_navigation_section_meeting(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = _fixture(self.config)
        request = testing.DummyRequest()
        va = _va(title='Upcoming', state='upcoming')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('Upcoming', response)

    def test_navigation_section_cookie(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = _fixture(self.config)
        request = testing.DummyRequest(cookies={'%s-%s' % (context.uid, 'upcoming'): 'closed'})
        va = _va(title='Upcoming', state='upcoming')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('Upcoming', response)

    def test_navigation_section_meeting_w_unread(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        self.config.include('voteit.core.testing_helpers.register_security_policies')
        self.config.scan('voteit.core.views.components.moderator_actions') #Due to changing security policy later on in test
        context = _fixture(self.config)
        #We don't use the actual security policy when rendering
        #FIXME: If we can set an actual policy that logs in a user, that would be much better..
        self.config.testing_securitypolicy(userid='dummy', permissive=True) #Bleh...
        request = testing.DummyRequest()
        va = _va(title='Nav w unread test', state='upcoming')
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('Nav w unread test', response)
        #This is a bit silly since it only checks for layout, but a better test than nothing
        self.assertIn('<span class="unread">(2)</span>', response)


class NavigationTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.navigation import navigation
        return navigation

    def test_navigation_unauthenticated(self):
        self.config.scan('voteit.core.views.components.navigation')
        context = testing.DummyModel()
        request = testing.DummyRequest()
        #va = _va()
        api = _api(context, request)
        self.assertEqual(u"", self._fut(context, request, None, api=api))

    def test_navigation_root(self):
        self.config.scan('voteit.core.views.components.navigation')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = _fixture(self.config)
        request = testing.DummyRequest()
        va = _va()
        api = _api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('Upcoming', response)

    def test_navigation_meeting(self):
        self.config.scan('voteit.core.views.components.navigation')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = _fixture(self.config)
        request = testing.DummyRequest()
        va = _va()
        api = _api(context.__parent__, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('Upcoming', response)


def _fixture(config):
    from voteit.core.models.agenda_item import AgendaItem
    from voteit.core.models.meeting import Meeting
    from voteit.core.models.proposal import Proposal
    from voteit.core.models.user import User
    from voteit.core.security import unrestricted_wf_transition_to
    request = testing.DummyRequest()
    root = bootstrap_and_fixture(config)
    root.users['dummy'] = User()
    root['m'] = meeting = Meeting()
    meeting.add_groups('dummy', ['role:Voter', 'role:Viewer'])
    meeting['ai1'] = AgendaItem()
    meeting['ai2'] = ai2 = AgendaItem()
    unrestricted_wf_transition_to(ai2, 'upcoming')
    ai2['p1'] = Proposal()
    ai2['p2'] = Proposal()
    meeting['ai3'] = ai3 = AgendaItem()
    unrestricted_wf_transition_to(ai3, 'upcoming')
    meeting['ai4'] = ai4 = AgendaItem()
    unrestricted_wf_transition_to(ai4, 'upcoming')
    return meeting

def _api(context=None, request=None):
    from voteit.core.views.api import APIView
    context = context and context or testing.DummyResource()
    request = request and request or testing.DummyRequest()
    return APIView(context, request)

def _va(name=None, title=None, **kwargs):
    class ViewAction():
        def __init__(self, name, title, kwargs):
            self.name = name
            self.title = title
            self.kwargs = kwargs
    return ViewAction(name, title, kwargs)
