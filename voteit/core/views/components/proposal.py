"""
JSON renderings for proposals.
This might be a bit mixed together with other html renderings.
"""
from betahaus.viewcomponent.decorators import view_action
from pyramid.traversal import resource_path


@view_action('proposal_json', 'text',
             directives = {'[data-json="text"]': 'obj.text'})
def text(context, request, va, **kw):
    return request.transform_text(context.text)

@view_action('proposal_json', 'creators_info',
             directives = {'[data-json="creators_info"]': 'obj.creators_info'})
def creators_info(context, request, va, **kw):
    return request.creators_info(context.creators)

@view_action('proposal_json', 'cogwheel',
             directives = {'[data-json="cogwheel"]': 'obj.cogwheel'})
def cogwheel_menu(context, request, va, **kw):
    if request.is_moderator:
        view = kw['view']
        return view.render_template('voteit.core:templates/snippets/cogwheel.pt', context = context)

@view_action('proposal_json', 'aid',
             directives = {'[data-json="aid"]+': 'obj.aid',
                           '[data-json="aid"]@href+': 'obj.aid'})
def aid(context, request, va, **kw):
    return context.aid

@view_action('proposal_json', 'aid-count',
             directives = {'[data-json="aid-count"]': 'obj.aid-count'})
def aid_count(context, request, va, **kw):
    path = resource_path(request.agenda_item)
    query = "path == '%s' and " % path
    query += "tags == '%s' and " % context.aid
    query += "type_name == 'DiscussionPost'"
    return int(request.root.catalog.query(query)[0])

@view_action('proposal_json', 'created',
             directives = {'[data-json="created"]': 'obj.created'})
def created(context, request, va, **kw):
    return request.localizer.translate(request.dt_handler.format_relative(context.created))

@view_action('proposal_json', 'metadata',
             directives = {'[data-json="metadata"]': 'obj.metadata'})
def metadata(context, request, va, **kw):
    view = kw['view']
    return view.render_view_group('metadata_listing', context)

@view_action('proposal_json', 'uid',
             directives = {'[data-uid]@data-uid': 'obj.uid'})
def uid(context, request, va, **kw):
    return context.uid
