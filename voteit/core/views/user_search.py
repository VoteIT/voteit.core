from arche.views.search import SearchView
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.i18n import TranslationString
from pyramid.view import view_config

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import MODERATE_MEETING


class MeetingSearchView(SearchView):

    @view_config(context=IMeeting, permission=MODERATE_MEETING, name='users_search_select2.json', renderer='json')
    def meeting_users_search_select_2_json(self):
        """ Special version that returns users from the root for moderators.
            This is for situations when you might want to att users to a meeting for instance.
        """
        id_attr = self.request.GET.pop('id_attr', 'uid')
        if id_attr != 'userid':
            raise HTTPBadRequest()
        self._mk_query()
        output = []
        limit = self.limit
        # Resolve ALL users here regardless of permissions. This view will be blocked
        for obj in self.request.resolve_docids(self.docids, perm=None):
            if limit > 0:
                type_title = getattr(obj, 'type_title', getattr(obj, 'type_name', "(Unknown)"))
                if isinstance(type_title, TranslationString):
                    type_title = self.request.localizer.translate(type_title)
                try:
                    tag = self.request.thumb_tag(obj, 'mini')
                except AttributeError:
                    tag = ''
                user_extra = id_attr == 'userid' and ' ({})'.format(obj.userid) or ''
                output.append({'text': obj.title + user_extra,
                               'id': getattr(obj, id_attr),
                               'type_name': obj.type_name,
                               'img_tag': tag,
                               'type_title': '' if user_extra else type_title})
                limit -= 1
        return {'results': output}
