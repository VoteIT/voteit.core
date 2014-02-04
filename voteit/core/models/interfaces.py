from zope.interface import Attribute
from zope.interface import Interface

from betahaus.pyracont.interfaces import IBaseFolder


#Content type interfaces
class IBaseContent(IBaseFolder):
    """ Base content type that stores values in non-attributes to avoid
        collisions between regular attributes and fields.
        It expects validation to be done on the form level.
    """

    title = Attribute("""
        Gets the title from the title field. Just a shorthand for doing the normal get_field_value.""")
    
    creators = Attribute("""
        The userids of the creators of this content.
        Normally just one.""")
    
    add_permission = Attribute("""
        Permission required to add this content""")
    
    content_type = Attribute("""
        Content type, internal name. It's not displayed anywhere.""")
    
    allowed_contexts = Attribute("""
        List of which contexts this content is allowed in. Should correspond to content_type.""")

    created = Attribute(
        """A TZ-aware datetime.datetime of when this was created in UTC time.""")

    modified = Attribute(
        "A TZ-aware datetime.datetime of when this was updated last in UTC time.")

    uid = Attribute("""
        Unique ID. Will be set on init. This must be unique throughout the whole site,
        so when writing functions to export or import content, you might want to
        check that this is really set to something else.""")

    schemas = Attribute(
        """ Dict that contains a mapping for action -> schema factory name.
            Example:{'edit':'site_root_edit_schema'}.""")

    custom_accessors = Attribute(
        """ Dict of custom accessors to use. The key is which field to override,
            value should be a string which represent a callable on this class, or a callable method.
            The accessor method must accept default and key as kwarg.
            Example:
            
            .. code-block:: python
            
               class Person(BaseContent):
                   custom_accessors = {'title': 'get_title'}
                   
                   def get_title(key=None, default=''):
                       return "Something else!"
            
            When get_field_value('title') is run, "Something else!" will be returned instead.
                """)

    custom_mutators = Attribute(
        """ Same as custon accessor, but the callable must accept a value.
            Method must also accept key as kwarg.
            
            Example:
            
            .. code-block:: python
            
               class Person(BaseContent):
                   custom_mutator = {'title': 'set_title'}
                   
                   def set_title(value, key=None):
                       assert isinstance(value, basestring)
                       #<etc...>
            """)

    custom_fields = Attribute(
        """ A dict of fields consisting of key (field name) and field factory name.
            A field type must be registered with that factory name.
            Example: {'wiki_text':'VersioningField'} if your register a field factory
            with the name 'VersioningField'.
            
            See documentation in betahaus.pyracont for more info.""")

    field_storage = Attribute(
        """ An OOBTree storage for field values. The point of exposing this
            is to enable bypass of custom mutators or accessors.""")

    def __init__(data=None, **kwargs):
        """ Initialize class. note that the superclass will create field storage etc
            on init, so it's important to run super.
            creators is required in kwargs, this class will try to extract it from
            current request if it isn't present.
            Also, owner role will be set for the first entry in the creators-tuple.
        """

    def suggest_name(parent):
        """ Suggest a name if this content would be added to parent.
            By default it looks in the title field, and transforms
            the first 20 chars to something usable as title.
        """

    def mark_modified():
        """ Set this content as modified. Will bypass custom mutators to avoid loops.
            The only way to customize this is to override it.
            Only set_field_appstruct will trigger this method.
            If you set a field any other way, you'll have to trigger it manually.
        """

    def get_field_value(key, default=None):
        """ Return field value, or default.
            The lookup order is as follows:
            - Check if there's a custom accessor.
            - Check if the field is a custom field.
            - Retrieve data from normal storage and return.
        """

    def set_field_value(key, value):
        """ Set field value.
            Will not send events, so use this if you silently want to change a single field.
            You can override field behaviour by either setting custom mutators
            or make a field a custom field.
        """
        
    def get_field_appstruct(schema):
        """ Return an appstruct based on schema. Suitable for use with deform.
            Example: If there's a schema with the field 'title', this method will
            return a dict with the following layout:
            {'title':<Value of title>}
            Fields that don't have a value won't be returned.
        """

    def set_field_appstruct(appstruct, notify=True, mark_modified=True):
        """ Set a field value from an appstruct. (A dict)
            Usually passed along by Deform.
            This equals running set_field_value for each key/value pair in a dict.
        """

    def get_custom_field(key):
        """ Return custom field. Create it if it doesn't exist.
            Will only work if key:field_type is specified in custom_fields attribute.
        """

    def get_content(content_type=None, iface=None, states=None, sort_on=None, sort_reverse=False):
        """ Returns contained items within this folder. Keywords are usually conditions.
            They're treated as 'AND'. Note that this is an expensive method to run, if you
            can use the catalog instead for something, it's a much better option.

            content_type
                Only return types of this content type.
                
            iface
                content must implement this interface
                
            states
                Only get content with this workflow state. Can be a list or a string.
            
            sort_on
                Key to sort on
            
            sort_reverse
                Reverse sort order
        """


class ISiteRoot(IBaseFolder):
    """ Singleton that is used as the site root.
        When added, it will also create a caching catalog with the
        attribute catalog."""
    users = Attribute("Access to the users folder. Same as self['users']")
    

class IUsers(IBaseFolder):
    """ Contains all users. """
    
    def get_user_by_email(email):
        """ Return a user object if one exist with that email address.
            (email addresses should be unique)
        """


class IUser(IBaseFolder):
    """ Content type for a user. Usable as a profile page. """
    
    userid = Attribute("The userid is always the same as __name__, meaning "
                       "that the name of the stored object must be the userid. "
                       "This enables you to do get(<userid>) on a Users folder, "
                       "and it makes it easy to check that each username is only used once.")

    auth_domains = Attribute("Contains domain information on different authentication systems.")

    def get_image_plugin():
        """ Get the currently selected plugin (adapter) that this user has selected for
            profile picture.
            If the selected system is broken it will return None and not default to anything.
        """

    def get_image_tag(size=40, **kwargs):
        """ Get image tag. Always square, so size is enough.
            Other keyword args will be converted to html properties.
            Appends class 'profile-pic' to tag if class isn't part of keywords.
            Will currently return gravatar url if nothing is selected, and not render an image if
            something goes wrong. (Like a broken plugin)
        """

    def get_password():
        """ Get password hash.
        """
    
    def set_password(value):
        """ Set password for user.
            value is the unencrypted password, it will be stored as a SHA1-hash.
        """

    def send_mention_notification(context, request):
        """ Sends an email when the user is mentioned in a proposal or a discussion post
        """


class IAgendaItem(IBaseFolder):
    """ Agenda item content """
    start_time = Attribute("""
        Return start time, if set. The value will be set by a subscriber when
        the Agenda Item enters the state 'ongoing'.
        The subscriber is located at: :func:`voteit.core.subscribers.timestamps.add_start_timestamp` 
    """)
    end_time = Attribute("""
        Return end time, if set. The value will be set by a subscriber when
        the Agenda Item enters the state 'closed'.
        The subscriber is located at: :func:`voteit.core.subscribers.timestamps.add_close_timestamp` 
    """)


class IMeeting(IBaseFolder):
    """ Meeting content type """
    start_time = Attribute("Start time for meeting")
    end_time = Attribute("End time for meeting")
    invite_tickets = Attribute("""
        Storage for InviteTickets. Works pretty much like a folder.""")

    def add_invite_ticket(email, roles, message, sent_by = None, overwrite = False):
        """ Create an invite ticket and add it do the invite_tickets storage.
            Note that this doesn't send the invitation.
            If the ticket was added, it will be returned.
        """

    def copy_users_and_perms(name, event = True):
        """ Copy users and their perms from a previous meeting.
            This is a low level function that shouldn't be exposed directly.
            It's a good idea to only let users copy permissions from meetings they're already
            moderators in.
        """


class IDiscussionPost(IBaseFolder):
    """ A discussion post.
    """

    mentioned = Attribute("""
        All users who've been mentioned within this discussion post.
        This is to make sure several notifications aren't set when anything is updated.
        It's a key/value storage with userid as key and a datetime as value. """)

    def add_mention(userid):
        """ Set a userid as mentioned. """

    def get_tags(default = ()):
        """ Return all used tags within this discussion post. """


class IProposal(IBaseFolder):
    """ Proposal content type
    
        Workflow states for proposals
        
        published
            Used in ongoing meetings. This proposal is a candidate for a future poll.
            
        retracted
            The person who wrote the proposal ('Owner' role) doesn't stand by it
            any longer and it won't be a candidate for a poll.
    
        voting
            is a locked state - this proposal is part of an ongoing poll. Other polls
            can't include this proposal while it's in this state, and owners can't retract
            it. If you delete a proposal that is in this state, it might crash the poll
            it's a part of.

        denied
            Proposal has been denied. It can't be included in polls or retracted.

        approved
            Proposal has been approved. It can't be retracted. If you want to include
            it in a poll again, you need to set it as published again.
            
        unhandled
            Set by moderators if they never handled the proposal for some reason.
                    
        Administrators and moderators have extra privileges on proposals if the agenda item hasn't closed.
        (This is simply to help editing things to avoid mistakes.) After that, the proposals will be locked
        without any option to alter them. In that case, the ACL table 'closed' is used.
    """
    mentioned = Attribute("""
        All users who've been mentioned within this discussion post.
        This is to make sure several notifications aren't set when anything is updated.
        It's a key/value storage with userid as key and a datetime as value. """)

    def add_mention(userid):
        """ Set a userid as mentioned. """

    def get_tags(default = ()):
        """ Return all used tags within this proposal. The automatically set id (hashtag) for this
            proposal will also be returned. """


class IPoll(IBaseFolder):
    """ Poll content type.
        Note that the actual poll method isn't decided by the poll
        content type. It calls a poll plugin to get that.
        See :mod:`voteit.core.models.interfaces.IPollPlugin` for more info on those.
    """
    start_time = Attribute("Polls start time")
    end_time = Attribute("Polls end time")
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

    def get_all_votes():
        """ Return a frozenset of all votes in this poll.
        """

    def get_voted_userids():
        """ Returns userids of all who've voted in this poll.
        """

    def render_poll_result(request, api, complete):
        """ Render poll result. Delegates this to plugin.
        """

    def close_poll():
        """ Close the poll, calculate and store the result.
        """

    def adjust_proposal_states(uid_states, request = None):
        """ Adjust the states of proposals to something.
            This method is normally called from a poll plugin to set
            approved or denied proposals. (If any)
            This method will catch any errors and notify the moderator
            rather than abort the transaction. Ie if a state can't be set
            for a specific proposal, it will simply inform the moderator
            of that and set the correct states for the other proposals that might
            have been specified.
            
            uid_states
                A dict of proposal uids and which state id they should change to.
            
            request
                A request object that can be passed along. Otherwise this method
                will try to fetch the current request.

        """

    def get_proposal_by_uid(uid):
        """ Return a proposal by its uid. Raises KeyError if it isn't found, since
            it shouldn't be used with uids that don't exist.
        """

    def create_reject_proposal():
        """ Create a reject proposal if it was specified in the edit form.
            This method might go away in the future.
        """


class IVote(Interface):
    """ Vote content type. This behaves different than other
        content types and it doesn't inherit other interfaces
        which means that you need to specify that something applies
        for an IVote context specifically.
        Votes can't be checked or inspected by admins or moderators either.
        Only the owner of the Vote has any kind of permissions here.
    """

    def set_vote_data(value, notify = True):
        """ Set vote data. The data itself could be anything passed
            along by the poll plugin.
        """
        
    def get_vote_data(default = None):
        """ Get the data. The poll plugin should know what to make of it.
        """


class ILogEntry(Interface):
    """ A persistent log entry. """

    created = Attribute("When it was created, in UTC time.")
    context_uid = Attribute("UID of the context that triggered this log entry.")
    message = Attribute("Message")
    tags = Attribute("Tags, works pretty much like categories for log entry.")
    userid = Attribute("userid, if a person triggered this event.")
    scripted = Attribute("If a script triggered the event, store script name/id here.")

    def __init__(context_uid, message, tags=(), userid=None, scripted=None):
        """ Create a log entry. """


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
        """ Handle claim of this ticket. Set permissions for meeting and
            set the ticket as closed.

            Called by ticket form - see:
            :func:`voteit.core.views.meeting.MeetingView.claim_ticket`
        """


class IAgendaTemplates(Interface):
    """ Contains all Agenda templates. """


class IAgendaTemplate(Interface):
    """ Agenda template content """
    
    def populate_meeting(meeting):
        """ Populate meeting with agenda items
        """


#Mixin class interfaces
class IWorkflowAware(Interface):
    """ Mixin class for content that needs workflow. """
    
    workflow = Attribute('Get the workflow for this content.')
    
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

    def current_state_title(request):
        """ Return (untranslated) state title for the current state. """


class ISecurityAware(Interface):
    """ Mixin for all content that should handle groups.
        Principal in this terminology is a userid or a group id.
    """
    
    def get_groups(principal):
        """ Return groups for a principal in this context.
            The special group "role:Owner" is never inherited.
        """

    def check_groups(groups):
        """ Check dependencies and group names. """

    def add_groups(principal, groups, event = True):
        """ Add groups for a principal in this context.
            If event is True, an IObjectUpdatedEvent will be sent.
        """

    def del_groups(principal, groups, event = True):
        """ Delete groups for a principal in this context.
            If event is True, an IObjectUpdatedEvent will be sent.
        """

    def set_groups(principal, groups, event = True):
        """ Set groups for a principal in this context. (This clears any previous setting)
            If event is True, an IObjectUpdatedEvent will be sent.
        """

    def get_security():
        """ Return the current security settings.
        """
    
    def set_security(value):
        """ Set current security settings according to value, that is a list of dicts with keys
            userid and groups.
            Warning! This method will also clear any settings for users not present in value!
            This method will send an IObjectUpdatedEvent.
        """

    def list_all_groups():
        """ Returns a set of all groups in this context. """


#Adapters
class IFlashMessages(Interface):
    """ Adapts a request object to add flash messages to the current session.
        Flash messages are short text strings stored in a session.
        
        The message itself is usually things like "Object updated" or other
        short system messages.
    """

    def add(msg, type='info', close_button=True):
        """ Add a flash message. Note that the current sessions we use
            can't store a lot of text - so keep it short and simple!

            msg
                Regular text, usually a translation string unless
                you don't want it to be translated for some reason.

            type
                Will be set as a css-class but has no other function.
                Currently 'info' and 'error' are common values.

            close_button
                Show a close button to enable the user to remove the message.
                Mostly a question of aesthetics.
        """

    def get_messages():
        """ Return a generator of all flash messages, if any exist.
            Note that generators are True even if they're empty.
            If you need to do checks against contents, convert them
            to a tuple or something similar first.
        """


class IUserTags(Interface):
    """ Adapter for things that can have usertags.
        The difference to normal tags is that users choose to stand behind them.
        Typical example would be 'like', but it might also be used for other functionality,
        like a dynamic rss feed.
    """
    tags_storage = Attribute("Storage for user tags")

    def add(tag, userid):
        """ Add a tag for a userid. Note that the tag shouldn't use non-ascii chars.
            Think of it as an id rather than a readable name.
        """

    def userids_for_tag(tag):
        """ Return a tuple of all userids that have added a specific tag.
        """

    def remove(tag, userid):
        """ Remove a tag for a specific userid. It won't raise an exception if
            the tag doesn't exist.
        """


class IPollPlugin(Interface):
    """ A plugin for a poll.
    """
    name = Attribute("Internal name of this plugin. Must be unique.")
    title = Attribute("Readable title that will appear when you select which"
                      "poll plugin to use for a poll.")
    description = Attribute("Readable description that will appear when poll is displayed.")


    def get_vote_schema(request=None, api=None):
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

    def render_result(request, api, complete=True):
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


class IAuthPlugin(Interface):
    """ Authentication plugin.
        This handles login, registration and rendering of those resources.
    """
    name = Attribute("""The name of this authentication method. It will be used to register
        this as an adapter,so it's a good idea to only use a-z and _.""")

    def __init__(context, request):
        """ Initialize.
        
            context
                Must be what this adapts, which in this case is the site root.
            
            request
                Current request.
        """

    def login(appstruct):
        """ Login a user. Any information in the appstruct is ment to be used by the plugin.
            This probably includes a userid, or perhaps a password to validate. With OpenID or similar,
            appstruct will be a URI. Note that this method must be implemented by the subclass that
            inherits this base. Note that the actual login is performed by the remember / HTTPFound methods.
            
            appstruct
                A dict containing relevant data to  perform login. For the most simple methods, it might just be a
                userid.

            .. code-block:: python
            
                from pyramid.security import remember
                from pyramid.httpexceptions import HTTPFound

                userid = appstruct['userid']
                user = self.context.users[userid]
                #<do something to validate that this userid is owned by whoever tries to login, and then...
                headers = remember(self.request, userid)
                #If url is passed along as a keyword in appstruct, redirect to that url
                url = appstruct.get('url', self.request.resource_url(self.context))
                return HTTPFound(location = url,
                                 headers = headers)
        """

    def register(appstruct):
        """ Register a user. Appropriate fields in this appstruct should be used to construct the new user object,
            or as information for some other storage system for user objects. You don't have to modify this
            view if you add fields to the registration schema. It will be saved to the user object.
            
            The following keys are required in the appstruct if you wish to use the default implementation.
            
            userid
                UserID picked by the user during the registration process. Must be unique.
            
            came_from
                A URL to send the user to when the process is finished. This is good to keep.
            
            email
                Users email
            
            first_name
                Users first name
            
            last_name
                Users last name            
        """

    def modify_login_schema(schema):
        """ Optional method to adjust the default login schema when this method is used.
            Any fields added there will be passed along to the login method aswell.
        
            schema
                An instantiated schema object.

            .. code-block:: python

                import colander

                schema.add(colander.SchemaNode(colander.String(),
                                               title = u"OpenID URL",
                                               name = 'open_id_url')
                                               validator = some_kind_of_validator)

            The above will add a field to the login schema when this method is used, which will
            cause the appstruct that's sent to the login method to contain a field called 'open_id_url'.
        """

    def modify_register_schema(schema):
        """ Optional method to adjust the default registration schema when this method is used.
            Any fields present here will be passed along to the set_field_appstruct and saved
            to the user object.
        
            schema
                An instantiated schema object.

            .. code-block:: python
            
                import colander
            
                schema.add(colander.SchemaNode(colander.String(),
                                               title = u"Your favourite band!",
                                               name = 'favourite_band'))
            
            This example will add a "Favourite band" field to registration, and store it to the newly registered user.
        """


class ILogHandler(Interface):
    """ An adapter that handle logging. """
    log_storage = Attribute("Storage for logs.")

    def __init__(context):
        """ Context to adapt. """
    
    def add(context_uid, message, tags=(), userid=None, scripted=None):
        """ Add a log entry.
            context_uid: the uid of the object that triggered logging.
            message: the message to store.
            tags: list of tags, works as a log category
            userid: if a user triggered the event, which user did so.
            scripted: if a script triggered the event, store script name here
        """


class ICatalogMetadata(Interface):
    """ An adapter to fetch metadata for the catalog.
        it adapts voteit.core.models.interfaces.ICatalogMetadataEnabled
        which is just a marker interface.
    """
    special_indexes = Attribute("A dict of iface:method name that should be run to extend the metadata for a specific iface.")
    
    def __init__(context):
        """ Object to adapt """
        
    def __call__():
        """ Return metadata for adapted object. """
    
    def get_agenda_item_specific(results):
        """ Update results with agenda item specific metadata. """


class IUnread(Interface):
    """ Adapter that provides unread functionality to an object.
        This means that all users who have access to the adapted object
        will have it marked as unread when it is added, or any other action that
        seems appropriate. (This is normally done with subscribers)
    """
    unread_storage = Attribute("Acts as a storage. Contains all userids of users who haven't read this context.")
    
    def mark_as_read(userid):
        """ Remove a userid from unread_userids if it exist in there.
            Just a convenience method in case the storage of userids change.
        """

    def get_unread_userids():
        """ Returns a frozenset of all userids who haven't read this context. """
        
    def reset_unread():
        """ Sets unread as newly created """


class IProposalIds(Interface):
    """ Computes and stores used proposal ids or automatic ids.
        They're used as hashtags and unique identifiers on proposals.
    """
    
    def add(userid, value):
        """ Create a tag for userid.
        """
        
    def get(userid):
        """ Get latets tag for userid
        """


class IProfileImage(Interface):
    """ Adapts a user object to serve profile image from different sources
    """
    name = Attribute("Adapters name, used like an id")
    title = Attribute("Human readable title")
    description = Attribute("Description of this profile image type and where it's from. Ment as information to help regular users.")

    def url(size):
        """ Return a URL to the profile picture, if no url could be created
            this function should return None
        
            size
                Prefered size of image. This is always a square, so you just specify the size as an int.
        """
        
    def is_valid_for_user():
        """ Checks if this adapter is usable with this user. Should return 'True' if it is.
        """


class IAccessPolicy(Interface):
    """ Adapts a meeting to handle an access policy. They're methods for granting
        access to users that request it.
    """
    name = Attribute("Works like an internal id for the access policy")
    title = Attribute("Readable title of the access policy. Should be a translation string")
    description = Attribute("Longer description to make it easier for moderators"
                            " to understand what this policy does. Also translation string")
    configurable = Attribute("Does this policy have any configuration options?")

    def is_public():
        """ Is this access policy configured so the meeting is public?
            Note: This feature might not be implemented yet. """

    def view(api):
        """ Render view """

    def view_submit(api):
        """ Handle a possibly submitted form, i.e. granting roles or doing something else. """

    def config_schema(api, **kw):
        """ Return a schema to be used for configuring this access policy. Optional. """

    def config_form(schema):
        """ Return a form for configuring access policy. """


#Utilities
class IDateTimeUtil(Interface):
    """ Utility that handles display of datetime formats.
        Also takes care of locale negotiation.
    """
    locale = Attribute("Currently set locale.")
    
    def set_locale(value):
        """ Set a new locale. """
    
    def d_format(value, format='short'):
        """ Return date formatted according to current locale."""

    def t_format(value, format='short'):
        """ Return time formatted according to current locale."""

    def dt_format(value, format='short'):
        """ Return date and time formatted according to current locale."""

    def tz_to_utc(datetime):
        """Convert the provided datetime object from local to UTC.

        The datetime object is expected to have the timezone specified in
        the timezone attribute.
        """

    def utc_to_tz(datetime):
        """Convert the provided datetime object from UTC to local.

        The resulting localized datetime object will have the timezone
        specified in the timezone attribute.
        """

    def localize(datetime, tz=None):
        """Localize a naive datetime to the provided timezone.

        If no timezone is provided, the current selected one is used.
        
        Example usage:
        from datetime.datetime import now
        #Regular python datetime:
        now_dt = now()
        #Converted to datetime that cares about a specific locale:
        self.localize(now_dt)
        """

    def utcnow():
        """Get the current datetime localized to UTC.

        The difference between this method and datetime.utcnow() is
        that datetime.utcnow() returns the current UTC time but as a naive
        datetime object, whereas this one includes the UTC tz info.
        """


class IJSUtil(Interface):
    """ """

    def add_translations(**tstrings):
        """ Add translationstrings to be included as:
            javascript_key = TranslationString
            Example: yes = _(u"Yes")
            The javascript key will be in the namespace translations in voteit.
            The above example can be found at:
            voteit.translations['yes']
        """

    def get_translations():
        """ Get a dict of all translations. This method may change to include
            conditions later. The dict is a copy of the original, so it's okay
            to modify it.
        """


class IFanstaticResources(Interface):
    """ Util for keeping track of when to render fanstatic resources.
        All resources doesn't have to be registered here, just use it
        when suitable. For instance, some widgets will include resources
        themselves. This is also a plug-point for custom skinning and similar.
    """
    order = Attribute("""
        A list of keys for resource order. You can change the order of rendered
        resources here. Later in the list means later rendering.""")

    def add(key, resource, discriminator = None):
        """ Add a resource.

            key
                Unique key for this resource. Just a string. If you
                specify the same key as something that exists, it will
                be overwritten by this registration.

            resource
                :term:`Fanstatic` resource to be included. Must be a
                Resource or Group object.

            discriminator
                A callable to be run with context, request and view as argument.
                If it returns something that is True, the resource will be
                included. Otherwise it won't. If this isn't set, the resource
                will always be included.
        """

    def include_needed(context, request, view):
        """ Runt need() on resources that are required in this context.
            Will go through all discriminators to check which resources that
            should be included in the order set in the order attribute.
            Returns keys of included resources.
        """


#Marker interfaces
class ICatalogMetadataEnabled(Interface):
    """ Marker interface for IBaseContent that should have metadata.
        The interface itself doesn't do anything, but the ICatalogMetadata
        adapter is registered for it.
    """
