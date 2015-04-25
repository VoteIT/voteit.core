"""
JSON renderings for discussion posts.
This might be a bit mixed together with other html renderings.
"""
from betahaus.viewcomponent.decorators import view_action
from pyramid.traversal import resource_path


@view_action('discussion_post_json', 'text',
             directives = {'[data-json="text"]': 'obj.text'})
def text(context, request, va, **kw):
    return request.transform_text(context.text)

@view_action('discussion_post_json', 'creators_info',
             directives = {'[data-json="creators_info"]': 'obj.creators_info'})
def creators_info(context, request, va, **kw):
    return request.creators_info(context.creators)

@view_action('discussion_post_json', 'cogwheel',
             directives = {'[data-json="cogwheel"]': 'obj.cogwheel'})
def cogwheel_menu(context, request, va, **kw):
    if request.is_moderator:
        view = kw['view']
        return view.render_template('voteit.core:templates/snippets/cogwheel.pt', context = context)

@view_action('discussion_post_json', 'created',
             directives = {'[data-json="created"]': 'obj.created'})
def created(context, request, va, **kw):
    return request.dt_handler.format_relative(context.created)

@view_action('discussion_post_json', 'metadata',
             directives = {'[data-json="metadata"]': 'obj.metadata'})
def metadata(context, request, va, **kw):
    view = kw['view']
    return view.render_view_group('metadata_listing', context)

@view_action('discussion_post_json', 'uid',
             directives = {'[data-uid]@data-uid': 'obj.uid'})
def uid(context, request, va, **kw):
    return context.uid
