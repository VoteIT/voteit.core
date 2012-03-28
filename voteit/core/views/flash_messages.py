from pyramid.renderers import render


FLASH_TEMPLATE = 'templates/snippets/flash_messages.pt'


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
