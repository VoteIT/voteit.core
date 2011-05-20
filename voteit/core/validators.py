import colander
from voteit.core import VoteITMF as _


def password_validation(node, value):
    """ check that password is
        - at least 6 chars and at most 100.
    """
    if len(value) < 6:
        raise colander.Invalid(node, _(u"Too short. At least 6 chars required."))
    if len(value) > 100:
        raise colander.Invalid(node, _(u"It's good to use secure passwords, but keep it under 100 chars will you?"))
    