
def evolve(root):
    """ Remove the index voted_userids, since it will cause concurrency errors
        if it exist whenever many users vote at the same time."""
    if 'voted_userids' in root.catalog:
        del root.catalog['voted_userids']
