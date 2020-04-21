

class TokenValidationError(Exception):
    """ A security token didn't match input value, or was never set. """


class BadPollMethodError(Exception):
    """ A user has picked a poll method that's really really really not suitable.
        (Puppies will die etc...)
        It will allow a force-bypass.
    """
    override_post_key = "override"
    override_confirmed = False

    def __init__(self, msg, poll, request):
        super(BadPollMethodError, self).__init__(msg)
        self.msg = msg
        self.poll = poll
        self.override_confirmed = bool(request.POST.get(self.override_post_key, False))
