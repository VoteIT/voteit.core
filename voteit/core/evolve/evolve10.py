from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal


def evolve(root):
    """ Change the Proposals and Discussion posts so title and text are separated.
    """
    from arche.utils import find_all_db_objects

    for obj in find_all_db_objects(root):
        if IProposal.providedBy(obj):
            try:
                obj.text = obj.field_storage.pop('title')
            except KeyError:
                pass
