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
    proposal_uids = Attribute("Contains a set of UIDs for all proposals this poll is about.")
    poll_plugin_name = Attribute("Returns the name of the selected voting utility.")

    def get_proposal_objects():
        """ Return all proposal objects resigered in this poll.
        """

    def get_voted_userids():
        """ Returns userids of all who've voted in this poll.
        """

    def get_ballots():
        """ Returns unique ballots and their counts. In the format:
            [{'ballot':x,'count':y}, <etc...>]
            The x in ballot can be any type of object. It's just what
            this polls plugin considers to be a vote.
        """

    def render_poll_result():
        """ Render poll result. Calls plugin to calculate result.
        """

class IVote(Interface):
    """ Vote content type.
    """

    def set_vote_data(value):
        """ Set vote data. The data itself could be anything passed
            along by the poll plugin.
        """
        
    def get_vote_data():
        """ Get the data. The poll plugin should know what to make of it.
        """


class IPollPlugin(Interface):
    """ A plugin for a poll.
    """
    name = Attribute("Internal name of this plugin. Must be unique.")
    title = Attribute("Readable title that will appear when you select which"
                      "poll plugin to use for a poll.")

    def get_vote_schema(poll):
        """ Return the schema of how a vote should be structured.
            This is used to render a voting form.
        """
    
    def get_vote_class():
        """ Get the vote class to use for this poll. Normally it's the
            voteit.core.models.vote.Vote class.
        """
        
    def get_settings_schema(poll):
        """ Get an instance of the schema used to render a form for editing settings.
        """

    def render_result(poll, ballots):
        """ Return rendered html with result display. Called by the poll view
            when the poll has finished.
        """