import urllib

import deform
import httpagentparser
from decimal import Decimal
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import remember
from pyramid.security import forget
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.arche_compat import createContent
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_login
from voteit.core.models.schemas import button_register
from voteit.core.models.schemas import button_save
from voteit.core.views.base_edit import BaseEdit


class SiteFormView(BaseEdit):

    @view_config(name="moderators_emails", context=ISiteRoot, renderer="templates/email_list.pt", permission=security.MANAGE_SERVER)
    def moderators_emails(self):
        """ List all moderators emails. """
        userids = set()
        for meeting in self.context.get_content(content_type = 'Meeting', states = ('ongoing', 'upcoming')):
            userids.update(security.find_authorized_userids(meeting, (security.MODERATE_MEETING,)))
        users = []
        for userid in userids:
            user = self.context.users.get(userid, None)
            if user:
                users.append(user)
        def _sorter(obj):
            return obj.get_field_value('email')
        self.response['users'] = tuple(sorted(users, key = _sorter))
        self.response['title'] = _(u"Email addresses of moderators with upcoming or ongoing meetings")
        return self.response
