
def evolve(root):
    """ Make sure all invite_ticket email addresses are lowercased. """
    for meeting in root.get_content(content_type = 'Meeting'):
        fix_this = set()
        for email in meeting.invite_tickets.keys():
            if email.lower() != email:
                fix_this.add(email)
        for email in fix_this:
            meeting.invite_tickets[email.lower()] = meeting.invite_tickets[email]
            del meeting.invite_tickets[email]
