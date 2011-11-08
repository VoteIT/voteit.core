""" Fanstatic lib"""
from fanstatic import Group
from fanstatic import Library
from fanstatic import Resource

from pkg_resources import resource_filename


#Libs
deformlib = Library('deform', resource_filename('deform', 'static'))
voteit_core_jslib = Library('voteit_js', 'js')
voteit_core_csslib = Library('voteit_css', 'css')

#CSS and JS
#jquery_16 = Resource(voteit_core_jslib, 'jquery-1.6.min.js')
jquery_142 = Resource(deformlib, 'scripts/jquery-1.4.2.min.js')

reset = Resource(voteit_core_csslib, 'reset.css') #Must be loaded before all other css!
voteit_main_css = Resource(voteit_core_csslib, 'main.css', depends=(reset,))

#jQuery UI
_jquery_ui_css = Resource(voteit_core_csslib, 'jquery-ui-1.8.16.custom.css', depends=(reset,))
_jquery_ui_js = Resource(voteit_core_jslib, 'jquery-ui-1.8.15.custom.min.js', depends=(jquery_142,))
jquery_ui = Group((_jquery_ui_css, _jquery_ui_js))

jquery_cookie = Resource(voteit_core_jslib, 'jquery.cookie.js', depends = (jquery_142,))
jquery_easy_confirm_dialog = Resource(voteit_core_jslib, 'jquery.easy-confirm-dialog.js', depends=(jquery_ui,))
jquery_rating = Resource(voteit_core_jslib, 'jquery.rating.js', depends=(jquery_142,))
tinymce = Resource(deformlib, 'tinymce/jscripts/tiny_mce/tiny_mce.js')

#qTip
_qtip_css = Resource(voteit_core_csslib, 'jquery.qtip.css', minified = 'jquery.qtip.min.css',
                     supersedes=(voteit_main_css,), depends = (reset,))
_qtip_js = Resource(voteit_core_jslib, 'jquery.qtip.js', minified = 'jquery.qtip.min.js',
                    depends = (jquery_ui,))
qtip = Group((_qtip_css, _qtip_js))

#textarea expander
jquery_textarea_expander = Resource(voteit_core_jslib, 'jquery.textarea-expander.js', depends = (jquery_142,))

#Deform
_deform_js = Resource(deformlib, 'scripts/deform.js')
_voteit_deform_css = Resource(voteit_core_csslib, 'deform.css', depends = (reset,))

jquery_form = Resource(deformlib, 'scripts/jquery.form.js', depends = (jquery_142,))
jquery_maskedinput = Resource(deformlib, 'scripts/jquery.maskedinput-1.2.2.min.js', depends = (jquery_142,))

#Timepicker
_jquery_timepicker_js = Resource(voteit_core_jslib, 'jquery-ui-timepicker-addon.js', depends=(jquery_ui,))
_jquery_timepicker_css = Resource(deformlib, 'css/jquery-ui-timepicker-addon.css', depends = (reset,))
jquery_timepicker = Group((_jquery_timepicker_css, _jquery_timepicker_js))

#VoteIT core
_star_rating_css = Resource(voteit_core_csslib, 'star_rating.css', depends=(voteit_main_css,))
star_rating = Group((_star_rating_css, jquery_rating))

voteit_common_js = Resource(voteit_core_jslib, 'voteit_common.js', depends=(jquery_142, jquery_cookie, qtip), bottom=True)
voteit_user_inline_info_js = Resource(voteit_core_jslib, 'voteit_user_inline_info.js', depends=(qtip, voteit_common_js), bottom=True)
_voteit_deform_js = Resource(voteit_core_jslib, 'voteit_deform.js', depends=(_deform_js,), bottom=True)
voteit_workflow_js = Resource(voteit_core_jslib, 'voteit_workflow.js', depends=(jquery_easy_confirm_dialog, voteit_common_js), bottom=True)

voteit_deform = Group((_voteit_deform_js, _voteit_deform_css))


DEFORM_RESOURCES = {
    'jquery': (jquery_142,),
    'jqueryui': (jquery_142, jquery_ui,),
    'jquery.form': (jquery_142, jquery_form,),
    'jquery.maskedinput': (jquery_142, jquery_maskedinput,),
    'datetimepicker': (jquery_142, jquery_timepicker,),
    'deform': (voteit_deform,),
    'tinymce': (tinymce,),
}
