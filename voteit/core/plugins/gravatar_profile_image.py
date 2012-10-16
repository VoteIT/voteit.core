from hashlib import md5

from zope.interface import implements
from zope.component import adapts

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IProfileImage


class GravatarProfileImagePlugin(object):
    implements(IProfileImage)
    adapts(IUser)
    
    name = u'gravatar_profile_image'
    title = _('Gravatar')
    description = _(u'profile_gravatar_explanation',
                    default=u'The profile image comes from the <a href="http://www.gravatar.com" target="_blank">Gravatar network</a>.' \
                    'It\'s taken from your current email address. If you want to change the picture, simply go to' \
                    'the Gravatar site and change your picture for the email you use in VoteIT.')
    
    def __init__(self, context):
        self.context = context
        
    def _generate_email_hash(self, email):
        """ Generat a md5 hash of an email address.
        """
        email = email.strip().lower()
        if email:
            return md5(email).hexdigest()
        return None
    
    def url(self, size):
        
        email_hash = self._generate_email_hash(self.context.get_field_value('email', ''))
        url = 'https://secure.gravatar.com/avatar/'
        if email_hash:
            url += email_hash
        url += '?d=mm&s=%(size)s' % {'size': size}
        
        return url
    
    def is_valid_for_user(self):
        return True


def includeme(config):
    """ Include gravatar plugin
    """
    config.registry.registerAdapter(GravatarProfileImagePlugin, (IUser,), IProfileImage, GravatarProfileImagePlugin.name)
