from pyramid.view import view_config
from arche.views.base import BaseView

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot


@view_config(name = "moderators_emails",
             context = ISiteRoot,
             renderer = "voteit.core:templates/users_emails.pt",
             permission = security.MANAGE_SERVER)
class ModeratorsEmails(BaseView):

    def __call__(self):
        """ List all moderators emails. """
        #FIXME: This method is way to expensive to use on a site with lots of users.
        userids = set()
        for meeting in self.catalog_search(resolve = True, type_name = 'Meeting', workflow_state = ('ongoing', 'upcoming')):
            userids.update(security.find_authorized_userids(meeting, (security.MODERATE_MEETING,)))
        users = []
        for userid in userids:
            user = self.context.users.get(userid, None)
            if user:
                users.append(user)
        def _sorter(obj):
            return obj.email
        response = {}
        response['users'] = tuple(sorted(users, key = _sorter))
        response['title'] = _(u"Email addresses of moderators with upcoming or ongoing meetings")
        return response
