from betahaus.viewcomponent import view_action


@view_action('agenda_item_widgets', 'dummy')
def dummy(context, request, va, **kw):
    return """hello"""
