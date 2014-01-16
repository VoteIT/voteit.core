from zope.interface import implements
from zope.component import queryAdapter
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.i18n import get_localizer
from BTrees.OOBTree import OOBTree 
from betahaus.pyracont.decorators import content_factory

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProfileImage
from voteit.core import VoteITMF as _
from voteit.core import security


USERID_REGEXP = r"[a-z]{1}[a-z0-9-_]{2,30}"


@content_factory('User', title=_(u"User"))
class User(BaseContent):
    """ User content type.
        See :mod:`voteit.core.models.interfaces.IUser`.
        All methods are documented in the interface of this class.
    """
    implements(IUser, ICatalogMetadataEnabled)
    content_type = 'User'
    display_name = _(u"User")
    allowed_contexts = ('Users',)
    add_permission = security.ADD_USER
    custom_mutators = {'title':'_set_title'}
    custom_fields = {'password':'PasswordField'}
    schemas = {'add': 'AddUserSchema', 'edit': 'EditUserSchema'}

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.CHANGE_PASSWORD, security.MANAGE_SERVER, )),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.CHANGE_PASSWORD,)),
               DENY_ALL]
    
    @property
    def userid(self):
        """ Convention - name should always be same as userid """
        return self.__name__
    
    @property
    def auth_domains(self):
        try:
            return self.__auth_domains__
        except AttributeError:
            self.__auth_domains__ = OOBTree()
            return self.__auth_domains__

    def get_image_plugin(self):
        #get selected adapter, fallback to gravatar. Will return None on ComponentLookupError.
        return queryAdapter(self,
                            name = self.get_field_value('profile_image_plugin', u'gravatar_profile_image'),
                            interface = IProfileImage)

    def get_image_tag(self, size=40, **kwargs):
        plugin = self.get_image_plugin()
        try:
            url = plugin.url(size)
        except Exception:
            #FIXME: Log exception
            url = None
        if not url:
            url = u"/static/images/default_user.png"
        tag = '<img src="%(url)s" height="%(size)s" width="%(size)s"' % {'url': url, 'size': size}
        for (k, v) in kwargs.items():
            tag += ' %s="%s"' % (k, v)
        if not 'class' in kwargs:
            tag += ' class="profile-pic"'
        tag += ' />'
        return tag

    def get_password(self):
        return self.get_field_value('password')
    
    def set_password(self, value):
        """ Encrypt a plaintext password. Convenience method for field password for b/c."""
        self.set_field_value('password', value)

    #Override title for users
    def _set_title(self, value, key=None):
        #Not used for user content type
        pass
    
    def _get_title(self):
        out = "%s %s" % ( self.get_field_value('first_name', ''), self.get_field_value('last_name', '') )
        return out.strip()

    title = property(_get_title, _set_title)
            
    def send_mention_notification(self, context, request):
        """ Sends an email when the user is mentioned in a proposal or a discussion post
        """
        # do not send mail if there is no emailadress
        if self.get_field_value('email'):
            locale = get_localizer(request)
            meeting = find_interface(context, IMeeting)
            agenda_item = find_interface(context, IAgendaItem)
            #FIXME: Email should use a proper template
            url = request.resource_url(context)
            link = "<a href=\"%s\">%s</a>" % (url, url)
            body = locale.translate(_('mentioned_notification',
                     default=u"You have been mentioned in ${meeting} on ${agenda_item}. Click the following link to go there, ${link}.",
                     mapping={'meeting':meeting.title, 'agenda_item': agenda_item.title, 'link': link,},))
            msg = Message(subject=_(u"You have been mentioned in VoteIT"),
                           recipients=[self.get_field_value('email')],
                           html=body)
            mailer = get_mailer(request)
            mailer.send(msg)
