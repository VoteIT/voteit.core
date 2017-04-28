# """ Fanstatic lib"""
from arche.fanstatic_lib import common_js
from arche.fanstatic_lib import main_css
from arche.fanstatic_lib import pure_js
from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from deform_autoneed import need_lib
from fanstatic import Library
from fanstatic import Resource
from js.bootstrap import bootstrap_css
from js.jquery import jquery
from js.jquery_tablesorter import tablesorter
from pkg_resources import resource_filename

# #Libs
deformlib = Library('deform', resource_filename('deform', 'static'))
voteit_core_jslib = Library('voteit_js', 'js')
voteit_core_csslib = Library('voteit_css', 'css')

base_js = Resource(voteit_core_jslib, 'base.js', depends = (common_js, jquery))
data_loader = Resource(voteit_core_jslib, 'data_loader.js', depends = (base_js, pure_js,))
unread_js = Resource(voteit_core_jslib, 'unread.js', depends = (base_js, data_loader))
watcher_js = Resource(voteit_core_jslib, 'watcher.js', depends = (data_loader,))
like_js = Resource(voteit_core_jslib, 'like.js', depends = (data_loader,))
support_js = Resource(voteit_core_jslib, 'support.js', depends = (data_loader,))

#voteit_bootstrap = Resource(voteit_core_csslib, 'voteit_bootstrap.css')
#Warning, bundling causes this resource to fail. It may have something to do with the css-map. (Probably not an accessible directory)
voteit_main_css = Resource(voteit_core_csslib, 'main.css', depends=(bootstrap_css, main_css), dont_bundle = True)

participants_js = Resource(voteit_core_jslib, 'participants.js', depends = (base_js, pure_js))

voteit_moderator_js = Resource(voteit_core_jslib, 'voteit_moderator.js', bottom = True, depends = (data_loader,))
voteit_manage_tickets_js = Resource(voteit_core_jslib, 'voteit_manage_tickets.js', bottom = True, depends=(tablesorter,))


def include_voteit_resources(view, event):
    voteit_main_css.need()
    watcher_js.need()
    need_lib('deform') #As a minimum this should be included, but it really depends on poll methods.
    if view.request.is_moderator:
        voteit_moderator_js.need()
    if view.request.meeting:
        unread_js.need()

def includeme(config):
    config.add_subscriber(include_voteit_resources, [IBaseView, IViewInitializedEvent])
