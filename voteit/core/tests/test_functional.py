import unittest


_settings = {
    'use': 'egg:voteit.core',
    'reload_templates': 'true',
    'debug_authorization': 'false',
    'debug_notfound': 'false',
    'debug_routematch': 'false',
    'debug_templates': 'true',
    'default_locale_name': 'en',
    'default_timezone_name': 'Europe/Stockholm',
    'available_languages': 'en sv',
    'zodb_uri': 'file://%(here)s/../var/Data.fs?connection_cache_size=20000',
    'sqlite_file': 'sqlite:///%(here)s/../var/sqlite.db',

    #VoteIT content types
    'content_types': """
                     voteit.core.models.agenda_item
                     voteit.core.models.discussion_post
                     voteit.core.models.invite_ticket
                     voteit.core.models.meeting
                     voteit.core.models.poll
                     voteit.core.models.proposal
                     voteit.core.models.site
                     voteit.core.models.user
                     voteit.core.models.users
                     """,

    #VoteIT settings
    'poll_plugins': 'voteit.schulze\nvoteit.core.plugins.majority_poll',

    #Set which mailer to include. pyramid_mailer.testing won't send any messages!
    #
    'mailer': 'voteit.core.tests.printing_mailer'
    }
#FIXME: This test doesn't work properly

#class FunctionalTests(unittest.TestCase):
#    def setUp(self):
#        from voteit.core import main
#        settings = _settings
#        app = main({}, **settings)
#        from webtest import TestApp
#        self.testapp = TestApp(app)
#
#    def test_root(self):
#        res = self.testapp.get('/', status=200)
#        self.failUnless('VoteIT' in res.body)
