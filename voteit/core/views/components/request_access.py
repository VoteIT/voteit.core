import colander
from deform import Form
from deform.exception import ValidationFailure
from betahaus.viewcomponent import view_action
from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPFound

from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_request
from voteit.core.models.schemas import button_cancel
from voteit.core import VoteITMF as _
from voteit.core.security import ROLE_VIEWER
from voteit.core.security import ROLE_DISCUSS
from voteit.core.security import ROLE_PROPOSE
from voteit.core.security import ROLE_VOTER
from voteit.core.models.interfaces import IMeeting

#FIXME: We repeat a lot of code here that could be refactored.

