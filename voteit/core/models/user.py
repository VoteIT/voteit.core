from hashlib import sha1
from BTrees.OOBTree import OOBTree
import colander

from voteit.core.models.base_content import BaseContent


def get_sha_password(password):
    """ Encode a plaintext password to sha1. """
    if isinstance(password, unicode):
        password = password.encode('UTF-8')
    return 'SHA1:' + sha1(password).hexdigest()


class User(BaseContent):
    """ Content type for a user. Usable as a profile page. """
    content_type = 'User'
    
    def get_password(self):
        self.get_field_value('password')
    
    def set_password(self, value):
        """ Encrypt a plaintext password. """
        if not isinstance(value, unicode):
            raise TypeError("Supplied password was not in Unicode")
        if len(value) < 5:
            raise ValueError("Password must be longer than 4 chars")
        value = get_sha_password(value)
        self.set_field_value('password', value)


class AddUserSchema(colander.Schema):
    userid = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(colander.String())
    first_name = colander.SchemaNode(colander.String())
    last_name = colander.SchemaNode(colander.String())
