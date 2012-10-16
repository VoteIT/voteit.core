import unittest

from pyramid import testing
from zope.interface.verify import verifyObject

    
class GravatarProfileImageUnitTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.plugins.gravatar_profile_image import GravatarProfileImagePlugin
        from voteit.core.models.user import User
        from voteit.core.models.site import SiteRoot 
        root = SiteRoot()
        root['user'] = User(email='hello@world.com')
        return GravatarProfileImagePlugin( root['user'] )

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IProfileImage
        obj = self._make_obj()
        self.assertTrue(verifyObject(IProfileImage, obj))

    def test_email_hash_method(self):
        obj = self._make_obj()
        email_hash = obj._generate_email_hash('hello@world.com')
        self.assertEqual(email_hash,
                         '4b3cdf9adfc6258a102ab90eb64565ea')
        
    def test_url_method(self):
        obj = self._make_obj()
        url = obj.url(size=45)
        self.assertEqual(url,
                         'https://secure.gravatar.com/avatar/4b3cdf9adfc6258a102ab90eb64565ea?d=mm&s=45')
    
    def test_is_valid(self):
        obj = self._make_obj()
        self.assertTrue(obj.is_valid_for_user())    

    