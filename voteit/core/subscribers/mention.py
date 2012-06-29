from repoze.folder.interfaces import IObjectAddedEvent
from pyramid.events import subscriber

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.helpers import at_userid_link


@subscriber([IProposal, IObjectAddedEvent])
@subscriber([IProposal, ObjectUpdatedEvent])
@subscriber([IDiscussionPost, IObjectAddedEvent])
@subscriber([IDiscussionPost, ObjectUpdatedEvent])
def transform_at_links(obj, event):
    old = obj.title
    text = at_userid_link(old, obj)
    if old != text:
        #This should notify as well
        obj.set_field_appstruct({'title': text})
