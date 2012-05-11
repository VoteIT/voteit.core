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



The Zope Component Architechture
--------------------------------

A large part of VoteIT and Pyramid is built on the Zope Component Architechture.
It's important to understand some of the basic concepts if you wish to do any
advanced modifications of VoteIT. A more complete guide is available at: TODO: ZCA-LINK

While it will make some code more hard to read and understand, it will make most parts
completely pluggable and changable, without latering any source code from other packages.

We'll go through some of the basic concepts that are used most within VoteIT.


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
 

   


