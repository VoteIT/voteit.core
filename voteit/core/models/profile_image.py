from zope.interface import implementer
from zope.component import adapter

from voteit.core.models.interfaces import IProfileImage
from voteit.core.models.interfaces import IUser


@implementer(IProfileImage)
@adapter(IUser)
class ProfileImagePlugin(object):
    name = u'' #Must be set by subclass
    title = u'' #Must be set by subclass
    description = u'' #Must be set by subclass
    
    def __init__(self, context):
        self.context = context
    
    def url(self, size):
        raise NotImplementedError()

    def is_valid_for_user(self):
        return False