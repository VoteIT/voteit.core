""" Fanstatic lib"""
from fanstatic import Group
from fanstatic import Library
from fanstatic import Resource
from pkg_resources import resource_filename
from js.jquery_tablesorter import tablesorter

#Libs
deformlib = Library('deform', resource_filename('deform', 'static'))
voteit_core_jslib = Library('voteit_js', 'js')
voteit_core_csslib = Library('voteit_css', 'css')

#CSS and JS
#jquery
jquery_deform = Resource(deformlib, 'scripts/jquery-1.7.2.min.js')

reset = Resource(voteit_core_csslib, 'reset.css') #Must be loaded before all other css!

#jQuery UI
_jquery_ui_css = Resource(voteit_core_csslib, 'jquery-ui-1.8.16.custom.css', depends=(reset,))
_jquery_ui_js = Resource(voteit_core_jslib, 'jquery-ui-1.8.15.custom.min.js', depends=(jquery_deform,))
jquery_ui = Group((_jquery_ui_css, _jquery_ui_js))

jquery_cookie = Resource(voteit_core_jslib, 'jquery.cookie.js', depends = (jquery_deform,))
jquery_easy_confirm_dialog = Resource(voteit_core_jslib, 'jquery.easy-confirm-dialog.js', depends=(jquery_ui,))
jquery_rating = Resource(voteit_core_jslib, 'jquery.rating.js', depends=(jquery_deform,))
jquery_caret = Resource(voteit_core_jslib, 'jquery.caret.js', depends=(jquery_deform,))
tinymce = Resource(deformlib, 'tinymce/jscripts/tiny_mce/tiny_mce.js')

#qTip
_qtip_css = Resource(voteit_core_csslib, 'jquery.qtip.css', minified = 'jquery.qtip.min.css', depends = (reset,))
_qtip_js = Resource(voteit_core_jslib, 'jquery.qtip.js', minified = 'jquery.qtip.min.js',
                    depends = (jquery_ui,))
qtip = Group((_qtip_css, _qtip_js))

#Deform
_deform_js = Resource(deformlib, 'scripts/deform.js', depends = (jquery_deform,))
_voteit_deform_css = Resource(voteit_core_csslib, 'deform.css', depends = (reset,))

jquery_form = Resource(deformlib, 'scripts/jquery.form-3.09.js', depends = (jquery_deform,))
jquery_maskedinput = Resource(deformlib, 'scripts/jquery.maskedinput-1.2.2.min.js', depends = (jquery_deform,))

#Timepicker
_jquery_timepicker_js = Resource(voteit_core_jslib, 'jquery-ui-timepicker-addon.js', depends=(jquery_ui,))
_jquery_timepicker_css = Resource(deformlib, 'css/jquery-ui-timepicker-addon.css', depends = (reset,))
jquery_timepicker = Group((_jquery_timepicker_css, _jquery_timepicker_js))

#Autoresize textarea
autoresizable_textarea_js = Resource(voteit_core_jslib, 'jquery.autoResizable.js', minified='jquery.autoResizable.min.js',
                                  depends = (jquery_deform,))


#VoteIT core
voteit_main_css = Resource(voteit_core_csslib, 'main.css', depends=(reset, _qtip_css,))

_star_rating_css = Resource(voteit_core_csslib, 'star_rating.css', depends=(voteit_main_css,))
star_rating = Group((_star_rating_css, jquery_rating))

voteit_common_js = Resource(voteit_core_jslib, 'voteit_common.js',
                            depends=(jquery_deform, jquery_cookie, qtip, jquery_caret, autoresizable_textarea_js),
                            bottom=True)
voteit_popups_js = Resource(voteit_core_jslib, 'voteit_popups.js', depends=(qtip, voteit_common_js), bottom=True)
_voteit_deform_js = Resource(voteit_core_jslib, 'voteit_deform.js', depends=(_deform_js,), bottom=True)
voteit_workflow_js = Resource(voteit_core_jslib, 'voteit_workflow.js', depends=(jquery_easy_confirm_dialog, voteit_common_js), bottom=True)
voteit_deform = Group((_voteit_deform_js, _voteit_deform_css))
voteit_participants = Resource(voteit_core_jslib, 'voteit_participants.js', bottom=True, depends=(voteit_popups_js, jquery_deform,))
voteit_participants_edit = Resource(voteit_core_jslib, 'voteit_participants_edit.js', bottom=True, depends=(voteit_participants,))
voteit_moderator_js = Resource(voteit_core_jslib, 'voteit_moderator.js', bottom=True, depends=(voteit_common_js,))
voteit_poll_js = Resource(voteit_core_jslib, 'voteit_poll.js', bottom=True, depends=(voteit_common_js,))
voteit_manage_tickets_js = Resource(voteit_core_jslib, 'voteit_manage_tickets.js', bottom=True, depends=(voteit_common_js, tablesorter))

DEFORM_RESOURCES = {
    'jquery': (jquery_deform,),
    'jqueryui': (jquery_deform, jquery_ui,),
    'jquery.form': (jquery_deform, jquery_form,),
    'jquery.maskedinput': (jquery_deform, jquery_maskedinput,),
    'datetimepicker': (jquery_deform, jquery_timepicker,),
    'deform': (jquery_deform, voteit_deform,),
    'tinymce': (tinymce,),
}


def is_base_view(context, request, view):
    """ View discriminators to check if a specific view does something.
        They're used by IFanstaticResources utility to determine which
        static resources to include, but it's possible to use them for
        other things as well.
    """
    from voteit.core.views.base_view import BaseView
    return isinstance(view, BaseView)

def is_participants_view(context, request, view):
    from voteit.core.views.participants import ParticipantsView
    return isinstance(view, ParticipantsView)

def is_participants_view_moderator(context, request, view):
    return view.api.show_moderator_actions and is_participants_view(context, request, view)

def is_agenda_item(context, request, view):
    return getattr(context, 'content_type', '') == 'AgendaItem'

def is_moderator(context, request, view):
    return view.api.show_moderator_actions

def is_votable_context(context, request, view):
    return getattr(context, 'content_type', '') in ('AgendaItem', 'Poll')

#Positional arguments
#key, resource, discriminator (if any)
DEFAULT_FANSTATIC_RESOURCES = (
    ('voteit_main_css', voteit_main_css),
    ('voteit_common_js', voteit_common_js),
    ('voteit_workflow_js', voteit_workflow_js),
    ('voteit_deform', voteit_deform),
    ('voteit_popups_js', voteit_popups_js),
    ('voteit_participants', voteit_participants, is_participants_view),
    ('voteit_participants_edit', voteit_participants_edit, is_participants_view_moderator),
    ('voteit_moderator_js', voteit_moderator_js, is_moderator),
    ('star_rating', star_rating, is_agenda_item), #Resources loaded with ajax, so this needs to be loaded in advance.
    ('voteit_poll_js', voteit_poll_js, is_votable_context), #Resources loaded with ajax, so this needs to be loaded in advance.
)
