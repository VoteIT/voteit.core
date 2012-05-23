from voteit.core.models.interfaces import IMeeting


def evolve(root):
    """ We have to remove the old feed entries so that they'll be
        recreated by the new voteit.feed package.
        VoteIT wasn't released on PyPI when this was written so
        it's okay to simply delete things here.
        We'll keep the old feed storage since voteit.feed might have
        been installed already.
    """
    _marker = object()
    broken_removed = 0
    for obj in root.get_content(iface = IMeeting):
        fs = getattr(obj, '__feed_storage__', _marker)
        if fs is _marker:
            continue
        keys_to_remove = []
        for (k, v) in fs.items():
            #Delete old broken objects?
            if v.__module__ == 'voteit.core.models.feeds':
                keys_to_remove.append(k)                

        for k in keys_to_remove:        
                del fs[k]
                broken_removed += 1

    print "Removed %s broken feed entry objects." % broken_removed
