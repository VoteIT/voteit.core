from repoze.folder import Folder

from voteit.core.models.agenda_item import AgendaItem, AgendaItemSchema
from voteit.core.models.meeting import Meeting, MeetingSchema
from voteit.core.models.poll import Poll, PollSchema, update_poll_schema
from voteit.core.models.proposal import Proposal, ProposalSchema
from voteit.core.models.site import SiteRoot, SiteRootSchema
from voteit.core.models.user import User
from voteit.core.models.users import Users, UsersSchema

class FactoryTypeInformation(Folder):
    """ Contains information about content types. The purpose of this
        is to handle generic creation of objects, and also provide information
        so we can store data in a dynamic way.
    """

class TypeInformation(object):
    """ schema: add schema for the content type.
        type_class: which class the content type is constructed from.
        omit_fields_on_edit: list of fieldnames to omit on edit. (like 'name')
        allowed_contexts: which contexts this type can be added to.
        add_permission: which permission is required to add.
        
        Any assignment that is None means None, which would mean that
        most types wouldn't be addable.
    """
    def __init__(self, schema, type_class, update_method=None):
        self.schema = schema
        self.type_class = type_class
        self.update_method = update_method
        for attr in ['omit_fields_on_edit', 'allowed_contexts',]:
            if not hasattr(self.type_class, attr):
                raise AttributeError("Class %s doesn't have the required attribute '%s'" % (self.type_class, attr))
    
    @property
    def omit_fields_on_edit(self):
        return self.type_class.omit_fields_on_edit
    
    @property
    def allowed_contexts(self):
        return self.type_class.allowed_contexts


#FIXME: This is temporary and should be a generic utility or similar later        
ftis = FactoryTypeInformation()
ftis[AgendaItem.content_type] = TypeInformation(AgendaItemSchema, AgendaItem)
ftis[Meeting.content_type] = TypeInformation(MeetingSchema, Meeting)
ftis[Poll.content_type] = TypeInformation(PollSchema, Poll, update_poll_schema)
ftis[Proposal.content_type] = TypeInformation(ProposalSchema, Proposal)
ftis[SiteRoot.content_type] = TypeInformation(SiteRootSchema, SiteRoot)
ftis[Users.content_type] = TypeInformation(UsersSchema, Users)
ftis[User.content_type] = TypeInformation(None, User) #Special case
