from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IMeeting


def evolve(root):
    """ Change all poll descriptions to plaintext. """
    from arche.interfaces import ICataloger
    from arche.utils import find_all_db_objects
    from webhelpers.html.render import sanitize

    #Move description to body
    root.body = root.description
    root.description = ""
    ICataloger(root).index_object()

    for obj in find_all_db_objects(root):
        if IPoll.providedBy(obj):
            #Turn description into plaintext
            obj.description = sanitize(obj.description)
            ICataloger(obj).index_object()
        elif IMeeting.providedBy(obj):
            #Move HTML field content to body
            obj.body = obj.description
            obj.description = ""
            ICataloger(obj).index_object()
