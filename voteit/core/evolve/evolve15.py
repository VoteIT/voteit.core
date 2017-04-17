from arche.interfaces import ICataloger
from arche.utils import find_all_db_objects
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


def _reorder_ais(meeting):
    order_priority = {}
    #Order will be blank so we must fetch the keys from data
    curr_keys = set(meeting.data.keys())
    if curr_keys != set(meeting.keys()):
        meeting.order = meeting.data.keys()
    for k in curr_keys:
        order_priority[k] = len(curr_keys)
    for ai in meeting.values():
        if not IAgendaItem.providedBy(ai):
            continue
        if 'order' in ai.field_storage:
            order_priority[ai.__name__] = ai.field_storage.pop('order')
    def _sorter(key):
        return order_priority[key]
    order = sorted(curr_keys, key=_sorter)
    meeting.order = order
    for obj in find_all_db_objects(meeting):
        cataloger = ICataloger(obj, None)
        if cataloger:
            cataloger.index_object()


def evolve(root):
    """ Reorder all agenda items + make sure keys are within order attribute.
    """
    if 'order' in root.catalog:
        del root.catalog['order']
    for obj in root.values():
        if IMeeting.providedBy(obj):
            _reorder_ais(obj)
