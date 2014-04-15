""" Note: Schema implementation is still experimental. It will be part of VoteIT,
    but don't rely too much on it right now.
    
    All of these should be treated as marker schemas, rather than exact implementations.
    The idea of providing them is simply to be able to create subscribers that can
    fire when a schema has been instatiated.
"""

from zope.interface import Interface


class ISchema(Interface):
    """ A colander schema. This should be a baseclass for most other schemas. """


class IEditUserSchema(ISchema):
    """ When editing user profile. """


class IAgendaItemSchema(ISchema):
    """ When adding or editing an Angenda item. """


class IProposalSchema(ISchema):
    """ Adding or editing a proposal. """


class ILayoutSchema(ISchema):
    """ Layout for meetings. """
