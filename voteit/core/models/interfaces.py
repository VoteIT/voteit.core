from zope.interface import Interface, Attribute


class IBaseContent(Interface):
    """ Base content type that stores values in non-attributes to avoid
        collisions between regular attributes and fields.
        It expects validation to be done on the form level.
    """
    
    def get_field_value(key, default=None):
        """ Get value. Return default if it doesn't exist. """

    def set_field_value(key, value):
        """ Store value in 'key' in storage. """
        
    def get_field_appstruct(schema):
        """ Return an appstruct based on schema. Suitable for use with deform.
            Example: If there's a schema with the field 'title', this method will
            return a dict with the following layout:
            {'title':<Value of title>}
            Fields that don't have a value won't be returned.
        """

    def set_field_appstruct(appstruct):
        """ Set a field value from an appstruct. (A dict)
            Usually passed along by Deform.
            This equals running set_field_value for each key/value pair in a dict.
        """

    uid = Attribute('UID')
    title = Attribute('Gets the title from the title field. '
                      'Exists so it can be overridden.')
    creators = Attribute('The userids of the creators of this content. '
                         'Normally just one. ')
    created = Attribute('When the object was created. (datetime.datetime)')
    add_permission = Attribute('Permission required to add this content')
    content_type = Attribute('Content type, internal name')
    allowed_contexts = Attribute('Which contexts is this type allowed in?')

    def get_content(content_type=None, iface=None, state=None, sort_on=None, sort_reverse=False):
        """ Returns contained items within this folder. Keywords are usually conditions.
            They're treated as 'AND'.
            keywords:
            content_type: Only return types of this content type.
            iface: content must implement this interface
            state: Only get content with this workflow state
            sort_on: Key to sort on
            sort_reverse: Reverse sort order
        """

class IWorkflowAware(Interface):
    """ Mixin class for content that needs workflow. """
    
    workflow = Attribute('Get the workflow for this content.')

    def initialize_workflow():
        """ Initialize workflow. The initial state will be set.
            If called twice, it will reset to the initial state.
        """
    
    def get_workflow_state():
        """ Get current workflow state. """
        
    def set_workflow_state(request, state):
        """ Set workflow state. Transition must be available to this state. (No warping ;) """

    def make_workflow_transition(request, transition):
        """ Set a state by specifying a specific transition to execute.
            This differs from set_workflow_state in the way that you can control
            which transition to execute, where set_workflow_state will just
            execute first available that it finds.
        """
    
    def get_available_workflow_states(request):
        """ Get all states that the current user can transition to from the current state.
        """


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


class ISiteRoot(Interface):
    """ Singleton that is used as the site root. """


class IUsers(Interface):
    """ Contains all users. """
    
    def get_user_by_email(email):
        """ Return a user object if one exist with that email address.
            (email addresses should be unique)
        """


class IUser(Interface):
    """ A user object. """
    
    userid = Attribute("The userid is always the same as __name__, meaning "
                       "that the name of the stored object must be the userid. "
                       "This enables you to do get(<userid>) on a Users folder, "
                       "and it makes it easy to check that each username is only used once.")
    
    def get_password():
        """ Get password hash.
        """
    
    def set_password(value):
        """ Set password for user.
            value is the unencrypted password, it will be stored as a SHA1-hash.
        """

    def new_request_password_token(request):
        """ Create a new password request token. Used for resetting a users password.
            It will email the link to reset password to that user.
        """
        
    def validate_password_token(node, value):
        """ Deform validator for password token. Ment to be used by Deform forms.
        """


class IAgendaItem(Interface):
    """ Agenda item content """


class IMeeting(Interface):
    """ Meeting content type """

    def add_invite_ticket(ticket, request):
        """ Add an invite ticket to the storage invite_tickets.
            It will also set the __parent__ attribute to allow
            lookup of objects. The parent of the ticket will
            in that case be the meeting.
        """

class IInviteTicket(Interface):
    """ Invite ticket - these track invitations to meetings. """
    email = Attribute("Email address this invite is for.")
    roles = Attribute("Roles to assign to this user once the ticket is used.")
    created = Attribute("Creation date")
    closed = Attribute("Close date (When the ticket was used)")
    token = Attribute("Security token that was part of the email. "
                      "Used in combinaton with an email address to gain entry to a meeting.")
    sent_dates = Attribute("A list of dates when an email was sent. (Each resend gets saved here)")
    claimed_by = Attribute("The userid of the user who claimed (used) this ticket.")
    
    def send(request):
        """ Send an invite or reminder to the email address that's set in
            the email attribute. Each time will be logged in sent_dates.
        """

    def claim(request):
        """ Use the ticket to gain access. Called by ticket form - see:
            views/meeting.py
        """


class IProposal(Interface):
    """ Proposal content type. """


class IPoll(Interface):
    """ Poll content type. """
    proposal_uids = Attribute("Contains a set of UIDs for all proposals this poll is about.")
    poll_plugin_name = Attribute("Returns the name of the selected voting utility.")
    ballots = Attribute("All ballots, set here after the poll has closed.")
    poll_result = Attribute("Result data that the poll plugin will set. Used for rendering the actual result.")
    poll_settings = Attribute("A dict of settings that the poll plugin might set from it's config_schema.")

    def get_poll_plugin():
        """ Preform a poll plugin lookup. Returns the poll plugin that is
            registered for this specific poll. Lookup uses the name set when the poll was added.
        """

    def get_proposal_objects():
        """ Return all proposal objects resigered in this poll.
        """

    def get_voted_userids():
        """ Returns userids of all who've voted in this poll.
        """

    def render_poll_result():
        """ Render poll result. Delegates this to plugin.
        """

    def close_poll():
        """ Close the poll, calculate and store the result.
        """

    def get_proposal_by_uid(uid):
        """ Return a proposal by its uid. Raises KeyError if it isn't found, since
            it shouldn't be used with uids that don't exist.
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


    def get_vote_schema():
        """ Return the schema of how a vote should be structured.
            This is used to render a voting form.
        """
    
    def get_vote_class():
        """ Get the vote class to use for this poll. Normally it's the
            voteit.core.models.vote.Vote class.
        """
        
    def get_settings_schema():
        """ Get an instance of the schema used to render a form for editing settings.
        """

    def handle_close():
        """ Handle closing of the poll.
        """

    def render_result():
        """ Return rendered html with result display. Called by the poll view
            when the poll has finished.
        """

    def change_states_of():
        """ This gets called when a poll has finished.
            It returns a dictionary with proposal uid as key and new state as value.
            Like: {'<uid>':'approved', '<uid>', 'denied'}
            It's not required to do, but if it isn't done, the proposals won't change state
            and you have to do it manually
        """

    def render_raw_data():
        """ Return rendered html with raw data from this poll.
            It should consist of ballot information, but be anonymised.
            The point with this view is to enable others to run
            a poll to verify the result.
            
            The method needs to return an instance of either:
            - pyramid.renderers.render
            - pyramid.response.Response
        """
        
class IContentTypeInfo(Interface):
    """ A content type info for VoteIT. Any content addable through
        the regular add menus needs one of these.
    """
    schema = Attribute("Schema class to use for this content")
    type_class = Attribute("Class to construct content from")
    
    allowed_contexts = Attribute("Return a list of content_type names where"
                                 "this content type is allowed. Taken from"
                                 "type_class.allowed_contexts.")
    add_permission = Attribute("Return add_permission from type_class - required to add content.")
    content_type = Attribute("Returns content_type attribute from type_class."
                    "Also used to identify the content type in the plugin like: util[<content_type>]")


class IContentUtility(Interface):
    """ The utility responsible for handling content types.
        All content type factories are registered with this utility.
        
        The utility itself inherits from repoze.folder.Folder which means it
        will behave like a regular folder.
        
        IContentTypeFactory types should be registered in the utility with the
        'add' method. See below.
    """
    def add(factory_obj, verify=True):
        """ Add ContentTypeInfo to the utility.
            factory_obj is an object that implements IContentTypeInfo
            verify if it's true the utility will check that IContentTypeInfo is
                implemented by the factory_obj.
        """

    def create(schema, type_class):
        """ Create a ContentTypeInfo object and return it. """

    def addable_in_type(content_type):
        """ Get all content type factories that are addable in the context of
            a content_type.
        """

class IExpressions(Interface):
    """ Handle user expressions like 'Like' or 'Support'.
        This behaves like an adapter on a sql db session.
    """
    
    def __init__(session):
        """ Object needs a session to adapt. """

    def add(tag, userid, uid):
        """ Add an expression. """

    def retrieve_userids(tag, uid):
        """ Retrieve a set of all userids who've set tag on uid. """

    def remove(tag, userid, uid):
        """ Remove where tag and userid and uid match. """

        
class ILogs(Interface):
    """ Handle logs.
        This behaves like an adapter on a sql db session.
    """
    
    def __init__(session):
        """ Object needs a request to adapt. """

    def add(meetinguid, message, tags=None, userid=None):
        """ Add a log entry. """
        
    def retrieve_entries(meetinguid, tags=None, userid=None):
        """ Retrieve a set of log entries in meetinguid. """


class IDiscussionPost(Interface):
    """ A discussion post.
    """


class IUnreads(Interface):
    """ Handle messages.
        This behaves like an adapter on a sql db session.
    """
    
    def __init__(session):
        """ Object needs a session to adapt. """

    def add(userid, contextuid):
        """ Add an unread. """
        
    def remove(userid, contextuid):
        """ Remove an unread. """
    
    def remove_user(userid):
        """ Remove an unread. """
        
    def remove_context(contextuid):
        """ Remove an unread. """
        
    def retrieve(userid, contextuid=None):
        """ Retrieve unreads. """


class ISQLSession(Interface):
    
    engine = Attribute("SQL engine")
    session_factory = Attribute("SQL session factory, must be a scoped session.")
    
    def __init__(engine):
        """ Engine to create a session from """
    
    def __call__():
        """ Returns session. """
