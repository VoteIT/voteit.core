from betahaus.viewcomponent import view_action
#from pyramid.renderers import render

from voteit.core import VoteITMF as _


@view_action('agenda_item_top', 'description')
def display_context_description(context, request, *args, **kwargs):
    """ Can be used in lots of places to simply get the context description. This is to make it orderable.
    """
    return """<div class="description">%s<div class="clear"><!-- --></div></div>""" % context.description
