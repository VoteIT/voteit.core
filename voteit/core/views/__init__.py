
def render_actionbar(view, **kw):
    """ Called from Arche to request an actionbar. We only show it for moderators and admins. """
    if not view.request.meeting and view.request.is_moderator:
        return view.render_template('arche:templates/action_bar.pt')

def includeme(config):
    config.include('.agenda_item')
    config.include('.cogwheel')
    config.scan(__name__)
