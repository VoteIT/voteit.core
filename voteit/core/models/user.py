from hashlib import sha1
from BTrees.OOBTree import OOBTree
import colander
import deform
from zope.interface import implements

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core import VoteITMF as _


def get_sha_password(password):
    """ Encode a plaintext password to sha1. """
    if isinstance(password, unicode):
        password = password.encode('UTF-8')
    return 'SHA1:' + sha1(password).hexdigest()


class User(BaseContent):
    """ Content type for a user. Usable as a profile page. """
    implements(IUser)
    content_type = 'User'
    allowed_contexts = ['Users']
    omit_fields_on_edit = [] #N/A for this content type

    def get_password(self):
        return self.get_field_value('password')
    
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
    password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5),
                widget=deform.widget.CheckedPasswordWidget(size=20),
                description=_(u'Type your password and confirm it'))
    email = colander.SchemaNode(colander.String())
    first_name = colander.SchemaNode(colander.String())
    last_name = colander.SchemaNode(colander.String())


class EditUserSchema(colander.Schema):
    email = colander.SchemaNode(colander.String())
    first_name = colander.SchemaNode(colander.String())
    last_name = colander.SchemaNode(colander.String())

class ChangePasswordSchema(colander.Schema):
    password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5),
                widget=deform.widget.CheckedPasswordWidget(size=20),
                description=_(u'Type your password and confirm it'))