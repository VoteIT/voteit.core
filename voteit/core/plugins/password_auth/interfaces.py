from zope.interface import Interface


class IPasswordHandler(Interface):

    def __init__(context):
        """ Context to adapt - in this case an IUser object. """

    def new_pw_token(request):
        """ Create a new password request token. Used for resetting a users password.
            It will email the link to reset password to that user.
        """

    def remove_password_token():
        """ Remove password token. """

    def token_validator(node, value):
        """ Validate password. """

    def get_token():
        """ Return password request token, or None.
        """

