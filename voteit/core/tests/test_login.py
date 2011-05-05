import unittest

from pyramid import testing


class FunctionalLoginTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_browser(self):
        #FIXME: We need to check proper testing of ZODB
        from zope.testbrowser.wsgi import Browser
        from voteit.core import main
        settings = {}
        settings['zodb_uri'] = "file:///tmp/Data.fs?connection_cache_size=20000"
        app = main({}, **settings)
        return Browser('http://localhost/', wsgi_app=app)

#    def test_failed_login(self):
#        browser = self._make_browser()
#        browser.getLink('Login').click()
#        self.assertEqual(browser.url, 'http://localhost/login')
#        
#        browser.getControl(name='userid').value = 'test'
#        browser.getControl(name='password').value = 'test'
#        browser.getControl('Log In').click()
#        self.assertEqual(browser.url, 'http://localhost/login')
#        self.failUnless('Login failed' in browser.contents)
#        