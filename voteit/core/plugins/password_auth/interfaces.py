from zope.interface import Interface


class IPasswordHandler(Interface):

    def __init__(context):
        """ Context to adapt - in this case an IUser object. """

