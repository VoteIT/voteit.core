from pyramid.interfaces import IDict
from zope.interface import Attribute
from zope.interface import Interface

from arche.interfaces import IBase
from arche.interfaces import IContent
from arche.interfaces import IIndexedContent
from arche.interfaces import IUser as IArcheUser


#Content type interfaces
class IBaseContent(IBase, IContent, IIndexedContent):
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

    created = Attribute(
        """A TZ-aware datetime.datetime of when this was created in UTC time.""")

    modified = Attribute(
        "A TZ-aware datetime.datetime of when this was updated last in UTC time.")

    uid = Attribute("""
        Unique ID. Will be set on init. This must be unique throughout the whole site,
        so when writing functions to export or import content, you might want to
        check that this is really set to something else.""")

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


class ISiteRoot(IBaseContent):
    """ Singleton that is used as the site root.
        When added, it will also create a caching catalog with the
        attribute catalog."""
    users = Attribute("Access to the users folder. Same as self['users']")
    

class IUsers(IBaseContent):
    """ Contains all users. """
    
    def get_user_by_email(email):
        """ Return a user object if one exist with that email address.
            (email addresses should be unique)
        """


class IUser(IBaseContent, IArcheUser):
    """ Content type for a user. Usable as a profile page. """

    def __init__(**kw):
        pass

    userid = Attribute("The userid is always the same as __name__, meaning "
                       "that the name of the stored object must be the userid. "
                       "This enables you to do get(<userid>) on a Users folder, "
                       "and it makes it easy to check that each username is only used once.")

    def get_image_plugin(request):
        """ Get the currently selected plugin (adapter) that this user has selected for
            profile picture.
            If the selected system is broken it will return None and not default to anything.
        """

    def get_image_tag(size=40, request = None, **kwargs):
        """ Get image tag. Always square, so size is enough.
            Other keyword args will be converted to html properties.
            Appends class 'profile-pic' to tag if class isn't part of keywords.
            Will currently return gravatar url if nothing is selected, and not render an image if
            something goes wrong. (Like a broken plugin)
        """


class IAgendaItem(IBaseContent):
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


class IMeeting(IBaseContent):
    """ Meeting content type """
    start_time = Attribute("Start time for meeting")
    end_time = Attribute("End time for meeting")
    invite_tickets = Attribute("""
        Storage for InviteTickets. Works pretty much like a folder.""")

    def add_invite_ticket(email, roles, sent_by = None):
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


class IDiscussionPost(IBaseContent):
    """ A discussion post.
    """
    tags = Attribute(""" Return all used tags within this discussion post. """)


class IProposal(IBaseContent):
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

    tags = Attribute("""
        Return all used tags within this proposal. The automatically set id (hashtag) for this
        proposal will also be returned. """)


class IPoll(IBaseContent):
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
            
            This method will probably be removed in the future and replaced by a catalog search.
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
    """ DEPRECATED: A persistent log entry. """

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


class IPollPlugin(Interface):
    """ A plugin for a poll.
    """
    name = Attribute("Internal name of this plugin. Must be unique.")
    title = Attribute("Readable title that will appear when you select which"
                      "poll plugin to use for a poll.")
    description = Attribute("Readable description that will appear when poll is displayed.")


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

    def render_result(view):
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


class ILogHandler(Interface):
    """ DEPRECATED: An adapter that handle logging. """
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


class IUserUnread(IDict):
    container_ifaces = Attribute("List of interfaces that should be considered as containers"
                                 "for unread items. Currently only AgendaItems within VoteIT.")
    counter_ifaces = Attribute("List of interfaces that should count a grand total of "
                               "their contained items. Essentially a cache so we don't "
                               "have to loop over all containers. Within VoteIT "
                               "currently only Meetings.")

    def add(context):
        """ Add context as unread. """

    def remove(context):
        """ Remove context from unread. """

    def remove_uids(container, uids):
        """ Remove uids from container - I.e they've been read or the
            container was deleted.
        """

    def get_count(container_uid, type_name):
        """ Number of unread within a container. """

    def get_uids(container_uid, type_name):
        """ Unread uids of a specific type, within a container.
        """

    def get_unread_count(counter_uid, type_name):
        """ Get result of counter. (Usually for meetings)
        """


class IProposalIds(Interface):
    """ Computes and stores used proposal ids (or automatic ids as they were called).
        They're used as hashtags and unique identifiers on proposals.
        
        The adapter itself adapts the meeting.
    """
    proposal_ids = Attribute("""
        Storage for the proposal ids. An OOBTree object which accepts dict-like operations.
        It keeps track of current last key for a specific proposal. What kind of keys
        it will track has to do with the implementation. It could be current key for a UserID
        or perhaps for a specific context. It's up to the add method to decide what to do with it. """)

    def add(proposal):
        """ Add an id for this proposal. It will update both the proposal and
            the global storage within the meeting.
        """


class IProfileImage(Interface):
    """ Adapts a user object to serve profile image from different sources
    """
    name = Attribute("Adapters name, used like an id")
    title = Attribute("Human readable title")
    description = Attribute("Description of this profile image type and where it's from. Ment as information to help regular users.")

    def url(size, request):
        """ Return a URL to the profile picture, if no url could be created
            this function should return None
        
            size
                Prefered size of image
            
            request
                Regular request object
        """
        
    def is_valid_for_user():
        """ Checks if this adapter is usable with this user
        """


class IMentioned(Interface):
    pass

class IAccessPolicy(Interface):
    """ Adapts a meeting to handle an access policy. They're methods for granting
        access to users that request it.
    """
    context = Attribute("Adapted context")
    name = Attribute("Works like an internal id for the access policy")
    title = Attribute("Readable title of the access policy. Should be a translation string")
    description = Attribute("Longer description to make it easier for moderators"
                            " to understand what this policy does. Also translation string")
    #configurable = Attribute("Does this policy have any configuration options?")
    view = Attribute("""
        Name of a custom view to redirect to. Should normally be None
        unless you want to do heavy customisations. """)

    def schema():
        """ If a form of some sort should be rendered, return a schema. """

    def handle_success(view, appstruct):
        """ If a schema existed, this gets called if it passed validation.
        """

    def config_schema():
        """ Return a schema to be used for configuring this access policy.
            Return None if you don't want any configuration options.
        """

    def handle_config_success(view, appstruct):
        """ Called when configuration schema passed validation.
        """

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

    def relative_time_format(time):
        """ Get a readable relative format like "5 minutes ago". """


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
