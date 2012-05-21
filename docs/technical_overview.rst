.. _technical_overview:

Technical overview
==================

Just to wet your aptetite, if you're into the technical stuff or just want a tutorial
of the technologies included in VoteIT.

Some quick facts

.. tabularcolumns:: |L|L|

======================== ==================
Programming language     :term:`Python`
Database                 :term:`ZODB`
Framework                :term:`Pyramid`
Schema library           :term:`colander`
Form library             :term:`deform`
Static serving (JS/CSS)  :term:`Fanstatic`
Web server               :term:`Paste` - but any WSGI-compatible can be used.
======================== ==================


.. _zca:

The Zope Component Architechture
--------------------------------

A large part of VoteIT and Pyramid is built on the Zope Component Architechture.
It's important to understand some of the basic concepts if you wish to do any
advanced modifications of VoteIT. A more complete guide is available at: TODO: ZCA-LINK

While it will make some code more hard to read and understand, it will make most parts
completely pluggable and changable, without latering any source code from other packages.

We'll go through some of the basic concepts commonly used within VoteIT. 


.. _registry:

Registry
^^^^^^^^

All components are stored within a registry, and retrieved from there. There's a global
registry, and an application (local) registry. Parts of VoteIT uses components that require
VoteITs registry to be global, so as far as we're concerned here, the global registry
and VoteITs local registry is basically the same thing.

Retrieving the registry within Pyramid can be done trough the method
``from pyramid.threadlocal import get_current_registry``.
It's also stored on the ``request`` object as an attribute - ``request.registry``.

When for a view is decorated with ``view_config`` or a view component with ``view_action``
or a content type with ``content_factory`` they'll all really be turned into components
within the local registry. That way, most app developers don't need to understand how
the component infrastructure works to use it.


.. _interfaces:

Interfaces
^^^^^^^^^^

Most components implement an interface. It's basically just a voluntary statement of what's to be
considered public code within a specific class. There are also marker interfaces, that simply state
that something is of a certain type.

This is an example of a marker interface implementation

  .. code-block:: py

   from zope.interface import Interface
   from zope.interface import implements


   class ICachable(Interface):
       """ Cache me! """


   class IDocument(Interface):
       """ I am a documet type """


   class Document(object):
       implements(IDocument, ICachable)


   class RichTextDocument(object):
       implements(IDocument)


Interfaces usually declair their function and what you could expect of them as well. Something
like this:

  .. code-block:: py

   class IDocument(Interface):
       """ I am a document with a title. """

       def get_title():
           """ Get the title of the document. """

       def set_title(value):
           """ Set the title of the document. """

Note that self is missing from the statement. When a class implements this interface, it needs to have the
methods specified in the interface.
 
The good thing about interfaces is that you can swap base clases and don't need to care about inheritance.
As long as you implement the interface correctly, everything should be fine.


.. _utilities:

Utilities
^^^^^^^^^

Another core concept is using utilities. It could pretty much be anything within the local app.

A commonly used utility within VoteIT is DateTimeUtil that implements the
:mod:´voteit.core.models.interfaces.IDateTimeUtil` interface. This utility is a regular class
that has a lot of functions for converting different time formats. It parses settings on init,
and is stored in memory as an object after that.

It's initalised this way:

  .. code-block:: py

    from voteit.core.models.interfaces import IDateTimeUtil
    from voteit.core.models.date_time_util import DateTimeUtil

    #Initialize the utility - just like any normal class
    util = DateTimeUtil('sv', 'Europe/Stockholm')

    #config here is an object that is passed to the function that starts an app
    #See pyramid docs. The local registry is stored there too.
    config.registry.registerUtility(util, IDateTimeUtil)

From now on, the utility will be in memory. Any changes you make to the object will be gone
when the application restarts.

To retrieve the utility, simply ask for something that implements its interface.

  .. code-block:: py

   from pyramid.threadlocal import get_current_registry

   from voteit.core.models.interfaces import IDateTime


   registry = get_current_registry()
   util = registry.getUtility(IDateTime)

If it isn't found, it will raise a ``ComponentLookupError``

The point of using utils is to make sure that objects implement an interface. If you remove
the standard utils and insert something else there that implements the same interface,i
everything will still work as expected.


.. _adapters:

Adapters
^^^^^^^^

Any application that expects others to extend or modify it will run into problems with subclassing
sooner or later. Especially if several plugins want to change or extend the same class. You'll end up
monkeypatching or simply hit a wall sooner or later.

A solution to this is revers dependency injection. Rather than something subclassing, it could wrap
the class it want to change instead. A typical example of this functionality is the PollPlugin adapter,
that enables a poll to use a specific method for votes.

Here's a document class that we'll want to extend. It's only function is to keep track of who's the
author of it...

  .. code-block:: py

    class Document(object):
        """ A document """

        def __init__(self, text = "", author = ""):
            self.set_text(text)
            self.set_author(author)

        def get_text(self):
            return self.__text__

        def set_text(self, value):
            self.__text__ = value

        def get_author(self):
            return self.__author__

        def set_author(self, value):
            self.__author__ = value

So lets say we want to add other functionality to this document, like a metadata collection:

  .. code-block:: py

    class MetadataAdapter(object):
        """ Fetches metadata from documents and return a dict. """

        def __init__(self, context):
            self.context = context

        def extract(self):
            """ Extract metadata """
            result = {}
            result['author'] = self.context.get_author()
            result['text'] = self.context.get_text()
            return result

Adapters always need to be passed the context they will adapt when they're constructed.
If you would execute the code straight away as it is, it would be something like this:

  .. code-block:: py

    context = Document(text = 'hello world', author = 'Robin')
    adapter = MetadataAdapter(context)
    adapter.extract()
    >>> {'author': 'Robin', 'text': 'hello world'}


.. _events:

Events
^^^^^^

Events are picked up by a subscriber. They're objects sent by the system to notify other parts of the
application that something has happened. An exelent plug point.

An event is created like this:

  .. code-block:: py

    class HelloWorldEvent(object):

        def __init__(self, message):
            self.message = message

    event = HelloWorldEvent('Hello world!')

To notify the system of your event, simply use the ``notify`` function.

  .. code-block:: py

    from zope.event import notify

    notify(event)

All events in VoteIT implement an interface too, which is the thing that subscribers subscribe to.
That means that you can change the base class and simply implement the interface in your new class
if you want to change it.

You can attach other criteria to an event as well. The most common of these are object events.
They're for a specific context. For instance, a meeting that changes workflow state will send an event.
Object events always have object as the first argument. This is an example:

  .. code-block:: py

    from zope.component.event import objectEventNotify

    class ObjectHighlightEvent(object):
        """ Event that fires when an object has been updated. """

        def __init__(self, object, msg, importance = 'low'):
            self.object = object
            self.msg = msg
            self.importance = importance

    #Let's send a notification for a made up context
    dummy_context = object()
    event = ObjectHighlightEvent(dummy_context, 'Stuff happend here!')
    objectEventNotify(event)


.. _subscribers:

Subscribers
^^^^^^^^^^^

To pick up an event from the system, create a subscriber. They're functions that will be executed
whenever a specific event takes place. Note that there's not special order in which they get picked up,
if you need that you must create subsequent events / subscribers.

To make creation of subscribers easy, Pyramid provides a decorator you can use. Here's an example
that will subscribe to every new ``request`` object created:

  .. code-block:: py

    from pyramid.events import subscriber
    from pyramid.interfaces import INewRequest

    @subscriber(INewRequest)
    def do stuff(event):
        print "I am the new request object: %s" % event.request

To use subscribers with object events, you need to provide an interface for object type and for the event.
This subscriber would fire whenever something that implements ``IDiscussionPost`` is added:

  .. code-block:: py

    from pyramid.events import subscriber
    from repoze.folder.interfaces import IObjectAddedEvent

    from voteit.core.models.interfaces import IDiscussionPost


    @subscriber([IDiscussionPost, IObjectAddedEvent])
    def do_stuff(obj, event):
        pass

Note the syntax difference - two positional arguments when there's two things to subscribe to.

See :mod:`voteit.core.subscribers` for more examples.

