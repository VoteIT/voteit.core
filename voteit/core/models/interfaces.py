from zope.interface import Interface, Attribute


class IBaseContent(Interface):
    """ Base content type that stores values in non-attributes to avoid
        collisions between regular attributes and fields.
        It expects validation to be done on the form level.
    """
    
    storage_key = Attribute("The key for a specific content type."
                            "Usually the content types own name or similar.")
    
    def set_field_value(key, value):
        """ Store value in 'key' in storage. """
        
    def get_field_value(key, default=None):
        """ Get value. Return default if it doesn't exist. """

class IAssignmentPlugin(Interface):
    """ """
    
    name = Attribute("This is the internal name, it will be used to later"
                     "retrieve the plugin so it needs to be unique")
    
    title = Attribute("A human friendly name.")
    