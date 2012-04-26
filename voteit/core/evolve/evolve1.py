from voteit.core.models.interfaces import IMeeting


def evolve(root):
    """ We have to remove the old feed entries so that they'll be
        recreated by the new voteit.feed package.
        VoteIT wasn't released on PyPI when this was written so
        it's okay to simply delete things here.
    """
    for obj in root.values():
        if IMeeting.providedBy(obj):
            if hasattr(obj, '__feed_storage__'):
                del obj.__feed_storage__
