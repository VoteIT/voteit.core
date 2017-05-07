from voteit.core import security


class ProposalInlineMixin(object):
    """ Ment to be used as mixin when one object is changed and
        should be returned inline.
    """

    def get_context_response(self):
        response = {}
        response['docids'] = [0]  # Not used
        response['unread_docids'] = ()
        response['contents'] = iter([self.context])
        response['hidden_count'] = False
        response['context'] = self.context.__parent__  # AI
        return response


class PollInlineMixin(object):
    """ Ment to be used as mixin when one object is changed and
        should be returned inline.
    """
    def get_context_response(self):
        response = {}
        response['contents'] = iter([self.context])
        response['vote_perm'] = security.ADD_VOTE
        response['context'] = self.context.__parent__  # AI
        response['show_add'] = False
        return response
