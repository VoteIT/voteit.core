import transaction

from voteit.core.models.interfaces import IMeeting

def evolve(root):
    # Remove old feed entries
    # Check if voteit.core.models.feed is importable
    try:
        import voteit.core.models.feed
    except ImportError:
        for obj in root.values():
            if IMeeting.providedBy(obj):
                if getattr(obj, '__feed_storage__', None):
                    del obj.__feed_storage__ 