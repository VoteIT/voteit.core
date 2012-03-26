.. _agenda_item_module:

:mod:`voteit.core.models.interfaces`
------------------------------------

.. automodule:: voteit.core.models.interfaces


Content type interfaces
-----------------------

These are persistent models - or content types. Most content types implement IBaseContent.
The exception is IVote, which should behave different.


  .. autointerface:: IBaseContent
     :members:

  .. autointerface:: ISiteRoot
     :members:

  .. autointerface:: IUsers
     :members:

  .. autointerface:: IUser
     :members:

  .. autointerface:: IAgendaItem
     :members:

  .. autointerface:: IMeeting
     :members:

  .. autointerface:: IInviteTicket
     :members:

  .. autointerface:: IAgendaTemplates
     :members:

  .. autointerface:: IAgendaTemplate
     :members:

  .. autointerface:: IFeedEntry
     :members:

  .. autointerface:: IProposal
     :members:

  .. autointerface:: IPoll
     :members:

  .. autointerface:: IVote
     :members:

  .. autointerface:: ILogEntry
     :members:

  .. autointerface:: IDiscussionPost
     :members:


Mixin classes
-------------
These are simple objects that require another class for persistance.
They're not usable at all by themselves.

  .. autointerface:: IWorkflowAware
     :members:

  .. autointerface:: ISecurityAware
      :members:
 


Adapters
--------

Adapters can extend functionality of other models. They're also easier to make
pluggable, compared to regular persistent models. 

  .. autointerface:: IUserTags
     :members:

  .. autointerface:: IPollPlugin
     :members:

  .. autointerface:: ILogHandler
     :members:

  .. autointerface:: IUnread
     :members:

  .. autointerface:: IFeedHandler
     :members:

  .. autointerface:: ICatalogMetadata
     :members:


Utilities
---------

Utilities are also pluggable models, but they don't require a specific context to operate on.
Most aren't persistent at all.

  .. autointerface:: IDateTimeUtil
     :members:


Markers
-------

Markers don't to anything themselves, but are rather mixin interfaces.
By setting a marker interface, you declare that you want something to happen
with a specific object.

  .. autointerface:: ICatalogMetadataEnabled
     :members:
