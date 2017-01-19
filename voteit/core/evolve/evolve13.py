
def evolve(root):
    """ Agenda items description field should've been stored
        as 'body' from the beginning.
    """
    for meeting in [x for x in root.values() if x.type_name == 'Meeting']:
        for ai in [x for x in meeting.values() if x.type_name == 'AgendaItem']:
            body = ai.description
            ai.update(body=body, description="")
