from zope.interface import Interface, Attribute


class IBaseContent(Interface):
    """ Base content type that stores values in non-attributes to avoid
        collisions between regular attributes and fields.
        It expects validation to be done on the form level.
    """
    
    def set_field_value(key, value):
        """ Store value in 'key' in storage. """
        
    def get_field_value(key, default=None):
        """ Get value. Return default if it doesn't exist. """

    uid = Attribute('UID')
    title = Attribute('Gets the title from the title field.'
                      'Exists so it can be overridden.')

class IUsers(Interface):
    """ Contains all users. """

class IUser(Interface):
    """ A user object. """

class IPoll(Interface):
    """ Poll content type. """

class IPollPlugin(Interface):
    """ A plugin for a poll. """
