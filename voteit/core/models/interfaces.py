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
    title = Attribute('Gets the title from the title field. '
                      'Exists so it can be overridden.')
    creators = Attribute('The userids of the creators of this content. '
                         'Normally just one. ')
    add_permission = Attribute('Permission required to add this content')
    content_type = Attribute('Content type, internal name')
    omit_fields_on_edit = Attribute('Remove the following keys from appstruct on edit. See base_edit.py for instance.')
    allowed_contexts = Attribute('Which contexts is this type allowed in?')

class ISecurityAware(Interface):
    """ Mixin for all content that should handle groups.
        Principal in this terminology is a userid or a group id.
    """
    
    def get_groups(principal):
        """ Return groups for a principal in this context.
            The special group "role:Owner" is never inherited.
        """

    def add_groups(principal, groups):
        """ Add a groups for a principal in this context.
        """
    
    def set_groups(principal, groups):
        """ Set groups for a principal in this context. (This clears any previous setting)
        """

    def update_from_form(value):
        """ Set permissions from a list of dicts with the following layout:
            {'userid':<userid>,'groups':<set of groups that the user should have>}.
        """

    def get_security_appstruct():
        """ Return the current settings in a structure that is usable in a deform form.
        """

    def list_all_groups():
        """ Returns a set of all groups in this context. """



class IUsers(Interface):
    """ Contains all users. """

class IUser(Interface):
    """ A user object. """

class IPoll(Interface):
    """ Poll content type. """
    
    proposals = Attribute("Contains a set of UIDs for all proposals this poll is about.")
    poll_plugin = Attribute("Returns the selected plugin utility.")


class IPollPlugin(Interface):
    """ A plugin for a poll. """
