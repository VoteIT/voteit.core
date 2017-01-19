from arche.views.base import BaseView
from betahaus.viewcomponent import render_view_group
from pyramid.response import Response

from voteit.core.security import MODERATE_MEETING
from voteit.core.models.interfaces import IBaseContent



class CogwheelMenuContent(BaseView):

    def __call__(self):
        return Response(render_view_group(self.context, self.request, 'context_actions', view = self))


def includeme(config):
    config.add_view(CogwheelMenuContent,
                    name = "__cogwheel_menu__",
                    permission = MODERATE_MEETING,
                    context = IBaseContent)
