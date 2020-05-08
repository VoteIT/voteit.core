from voteit.core import security


class ProposalInlineMixin(object):
    """ Ment to be used as mixin when one object is changed and
        should be returned inline.
    """

    def get_context_response(self):
        response = {
            "docids": [0],
            "unread_docids": (()),
            "contents": iter([self.context]),
            "hidden_count": False,
            "context": self.context.__parent__,
            "ck_mod": lambda obj: self.request.has_permission(
                security.MODERATE_MEETING, self.context
            ),
        }
        # A more expensive but accurate permission check for a specific object.
        return response


class PollInlineMixin(object):
    """ Ment to be used as mixin when one object is changed and
        should be returned inline.
    """

    def get_context_response(self):
        response = {
            "contents": iter([self.context]),
            "vote_perm": security.ADD_VOTE,
            "context": self.context.__parent__,
            "show_add": False,
        }
        return response
