from hashlib import md5

from zope.interface import implementer
from zope.component import adapter

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IProfileImage


@implementer(IProfileImage)
@adapter(IUser)
class GravatarProfileImagePlugin(object):
    name = u'gravatar_profile_image'
    title = _('Gravatar')
    description = _(u'profile_gravatar_explanation',
                    default=u'The profile image comes from the <a href="http://www.gravatar.com" target="_blank">Gravatar network</a>.' \
                    'It\'s taken from your current email address. If you want to change the picture, simply go to' \
                    'the Gravatar site and change your picture for the email you use in VoteIT.')
    
    def __init__(self, context):
        self.context = context

    def url(self, size, request):
        url = 'https://secure.gravatar.com/avatar/'
        email = self.context.get_field_value('email', '').strip().lower()
        if email:
            url += md5(email).hexdigest()
        url += '?s=%s' % size
        url += '&d=%s' % request.registry.settings.get('voteit.gravatar_default', 'mm')
        return url

    def is_valid_for_user(self):
        return True


def includeme(config):
    """ Include gravatar plugin
    """
    config.registry.registerAdapter(GravatarProfileImagePlugin, name = GravatarProfileImagePlugin.name)
