from unittest import TestCase

from pyramid import testing


class UserSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.subscribers.user')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.user import User
        return User()

    def test_generate_email_hash(self):
        obj = self._make_obj()
        obj.set_field_appstruct({'email': 'hello@world.com'})
        
        self.assertEqual(obj.get_field_value('email_hash'),
                         '4b3cdf9adfc6258a102ab90eb64565ea')

