from pyramid.events import subscriber
from repoze.folder.interfaces import IObjectAddedEvent

from voteit.core.models.interfaces import IUser
from voteit.core.interfaces import IObjectUpdatedEvent


@subscriber([IUser, IObjectAddedEvent])
@subscriber([IUser, IObjectUpdatedEvent])
def generate_email_hash(obj, event):
    """ Generate an email hash for the users who just changed his/her profile.
        Has to do with gravatar profile images.
    """
    obj.generate_email_hash()