"""
Macros here are stand-alone code parts that could be executed as a view or
imported and run from another view class, like APIView.
The reason for this is to allow them to be included in templates and to
be reloaded by Ajax requests.
"""
from pyramid.view import view_config
from pyramid.renderers import render, get_renderer


FLASH_TEMPLATE = 'templates/macros/flash_messages.pt'

class FlashMessages(object):
    
    def __init__(self, request):
        self.request = request
    
    def _get_messages(self):
        for message in self.request.session.pop_flash():
            yield message

    def __call__(self):
        response = dict(messages = self._get_messages(),)
        return render(FLASH_TEMPLATE, response, request=self.request)
    
    def add(self, msg, type='info', close_button=True):
        flash = {'msg':msg, 'type':type, 'close_button':close_button}
        if not hasattr(self.request, 'session'):
            #FIXME: Import proper logger
            return
        self.request.session.flash(flash)

    @view_config(name="_flash_messages", renderer=FLASH_TEMPLATE)
    def inline(self):
        response = dict(messages = self._get_messages(),)
        return response

