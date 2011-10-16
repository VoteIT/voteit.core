from pyramid.events import subscriber
from zope.component.event import objectEventNotify
from betahaus.pyracont.interfaces import IObjectUpdatedEvent

from voteit.core.events import ObjectUpdatedEvent


@subscriber(IObjectUpdatedEvent)
def compatibility_notify_object_updated(event):
    """ This method subscribes to betahaus.pyracont's version of ObjectUpdatedEvent,
        and simply calls voteit's version of the same object.
        This is for backwards compatibility.
    """
    new_event = ObjectUpdatedEvent(event.object, indexes=event.fields, metadata=True)
    objectEventNotify(new_event)
