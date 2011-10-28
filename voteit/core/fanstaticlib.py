""" Fanstatic lib"""
from fanstatic import Group
from fanstatic import Library
from fanstatic import Resource


from pkg_resources import resource_filename


#Libs
deform_static = Library('deform', resource_filename('deform', 'static'))
voteit_core_js = Library('voteit_js', 'js')
voteit_core_css = Library('voteit_css', 'css')


#CSS and JS
jquery_16 = Resource(voteit_core_js, 'jquery-1.6.min.js')
jquery_142 = Resource(deform_static, 'scripts/jquery-1.4.2.min.js')

reset = Resource(voteit_core_css, 'reset.css')
voteit_main_css = Resource(voteit_core_css, 'main.css', depends=(reset,))

#jQuery UI
_jquery_ui_css = Resource(voteit_core_css, 'smoothness/jquery-ui-1.8.16.custom.css')
_jquery_ui_js = Resource(voteit_core_js, 'jquery-ui-1.8.15.custom.min.js', depends=(jquery_142,))
jquery_ui = Group((_jquery_ui_css, _jquery_ui_js))

jquery_form = Resource(deform_static, 'scripts/jquery.form.js', depends = (jquery_142,))
jquery_maskedinput = Resource(deform_static, 'scripts/jquery.maskedinput-1.2.2.min.js', depends = (jquery_142,))
jquery_cookie = Resource(voteit_core_js, 'jquery.cookie.js', depends = (jquery_142,))
jquery_easy_confirm_dialog = Resource(voteit_core_js, 'jquery.easy-confirm-dialog.js', depends=(jquery_ui,))
jquery_rating = Resource(voteit_core_js, 'jquery.rating.js', depends=(jquery_142,))
tinymce = Resource(deform_static, 'tinymce/jscripts/tiny_mce/tiny_mce.js')

#qTip
_qtip_css = Resource(voteit_core_css, 'jquery.qtip.css')
_qtip_js = Resource(voteit_core_js, 'jquery.qtip.js', depends = (jquery_ui,))
qtip = Group((_qtip_css, _qtip_js))

#Timepicker
_jquery_timepicker_js = Resource(deform_static, 'scripts/jquery-ui-timepicker-addon.js', depends=(jquery_142,))
_jquery_timepicker_css = Resource(deform_static, 'css/jquery-ui-timepicker-addon.css')
jquery_timepicker = Group((_jquery_timepicker_css, _jquery_timepicker_js))

#Deform
_deform_js = Resource(deform_static, 'scripts/deform.js', depends=(jquery_form,))
_deform_css = Resource(deform_static, 'css/form.css', supersedes=(voteit_main_css,))
deform = Group((_deform_js, _deform_css))

#voteit.core ajax
voteit_ajax = Resource(voteit_core_js, 'ajax.js', depends=(jquery_142, jquery_cookie))




DEFORM_RESOURCES = {
    'jquery': jquery_142,
    'jqueryui': jquery_ui,
    'jquery.form': jquery_form,
    'jquery.maskedinput': jquery_maskedinput,
    'datetimepicker': jquery_timepicker,
    'deform': deform,
    'tinymce': tinymce,
}