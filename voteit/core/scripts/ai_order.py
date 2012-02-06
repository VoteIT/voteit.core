import transaction

from voteit.core.scripts.worker import ScriptWorker
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem


def update_order(*args):
    worker = ScriptWorker('sort_index')
    
    print "Adding sort index to agenda items"

    for meeting in worker.root.values():
        if IMeeting.providedBy(meeting):
            ais = [] 
            for ai in meeting.values():
                if IAgendaItem.providedBy(ai):
                    ais.append(ai)
            
            ais = sorted(ais, key=lambda k: k.get_field_value('start_time'))
            order = 0
            for ai in ais:
                ai.set_field_appstruct({'order': order})
                order += 1

    print "Committing to database"
    transaction.commit()
    
    print "Done"
    worker.shutdown()
    