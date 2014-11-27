# -*- coding: utf-8 -*-

import unittest

from pyramid import testing
from pyramid.i18n import TranslationString

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import active_poll_fixture


class AtUseridLinkTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import at_userid_link
        return at_userid_link
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_function(self):
        from voteit.core.interfaces import IWorkflowStateChange
        value = self._fut('@admin', self._fixture())
        self.assertIn('/m/_userinfo?userid=admin', value)


class GenerateSlugTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import generate_slug
        return generate_slug
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_unique(self):
        context = self._fixture()
        value = self._fut(context, u'o1')
        self.assertIn(u'o1', value)
        
    def test_same(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal 
        context['o1'] = Proposal()
        value = self._fut(context, u'o1')
        self.assertIn(u'o1-1', value)
        
    def test_cant_find_unique(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal
        context[u'o1'] = Proposal()
        for i in range(1, 101):
            context[u'o1-%s' % i] = Proposal()
        self.assertRaises(KeyError, self._fut, context, u'o1')
        

class Tags2linksTests(unittest.TestCase):
    
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request = self.request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import tags2links
        return tags2links

    def test_simple(self):
        value = self._fut("#hello world!")
        self.assertEqual(u'<a href="?tag=hello" class="tag">#hello</a> world!', value)

    def test_non_ascii(self):
        value = self._fut(u'#åäöÅÄÖ')
        self.assertIn(u'?tag=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96', value)

    def test_several_tags_and_br(self):
        value = self._fut(u"Men #hörni, visst vore det väl trevligt med en #öl?")
        self.assertIn(u'Men <a href="?tag=h%C3%B6rni" class="tag">#h\xf6rni</a>,', value)
        self.assertIn(u'en <a href="?tag=%C3%B6l" class="tag">#\xf6l</a>?', value)

    def test_existing_tags_not_touched(self):
        value = self._fut(u'<a>#tag</a>')
        self.assertEqual(u'<a>#tag</a>', value)

    def test_several_tags_twice(self):
        first = self._fut(u"Men #hörni, visst vore det väl trevligt med en #öl?")
        second = self._fut(first)
        self.assertEqual(first, second)

    def test_text_before_tag_negates_conversion(self):
        value = self._fut(u'this#that?')
        self.assertEqual(u'this#that?', value)

    def test_html_entities(self):
        value = self._fut(u'this#that?')
        self.assertEqual(u'this#that?', value)

class StripAndTruncateTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import strip_and_truncate
        return strip_and_truncate

    def test_strip_and_truncate(self):
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris at enim nec nunc facilisis semper. Sed vel magna sit amet augue aliquet rhoncus metus."
        truncated = self._fut(text, 100)
        self.assertEqual(truncated, 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris at enim nec nunc facilisis semper. S&lt;...&gt;') 


class SendEmailTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
        #self.config.registry.settings['']
        self.config.include('pyramid_mailer.testing')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.helpers import send_email
        return send_email

    def test_convert_html(self):
        html = "<p>Hello!</p>"
        msg = self._fut(subject = 'subject', recipients = 'john@doe.com', html = html)
        self.assertEqual(msg.body, u"Hello!")

    def test_recipients_always_tuple(self):
        html = "<p>Hello!</p>"
        msg = self._fut(subject = 'subject', recipients = 'john@doe.com', html = html)
        self.assertEqual(msg.recipients, ('john@doe.com',))

    def test_subject_translated(self):
        self.config.add_translation_dirs('voteit.core:locale/')
        self.config.registry.settings['default_locale_name'] = 'sv'
        html = "<p>Hello!</p>"
        subject = TranslationString(u'Reply', domain = 'voteit.core')
        msg = self._fut(subject = subject, recipients = 'john@doe.com', html = html)
        self.assertEqual(msg.subject, u'Svara')

    def test_plaintext_not_created_if_specified(self):
        html = "<p>Hello!</p>"
        plaintext = "Other stuff"
        msg = self._fut(subject = 'subject', recipients = 'john@doe.com', html = html, plaintext = plaintext)
        self.assertEqual(msg.body, plaintext)

    def test_plaintext_not_created_if_false(self):
        html = "<p>Hello!</p>"
        plaintext = ""
        msg = self._fut(subject = 'subject', recipients = 'john@doe.com', html = html, plaintext = plaintext)
        self.assertEqual(msg.body, None)

#FIXME: Current implementation of testing mailer behaves diffrently from the real one. Follow up!
#    def test_default_sender_included(self):
#        self.config.registry.settings['mail.default_sender'] = "VoteIT noreply <noreply@mailer.voteit.se>"
#        html = "<p>Hello!</p>"
#        msg = self._fut(subject = 'subject', recipients = 'john@doe.com', html = html)
#        self.assertEqual(msg.sender, u"")

