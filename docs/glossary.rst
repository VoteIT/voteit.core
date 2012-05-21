.. _glossary:

Glossary
========

.. glossary::
   :sorted:

   Adapter

    Part of the :term:`Zope Component Architechture`.
    A class that wraps another class and extends its functionality.
    Short intro at: :ref:`adapters`.

   Buildout

    `Buildout <http://www.buildout.org>`_ is a Python-based build system for creating, assembling and deploying applications
    from multiple parts, some of which may be non-Python-based. It lets you create a buildout
    configuration and reproduce the same software later.

    By using it, you don't have to care about a specific package or dependency beeing available
    on your platform. It also isolates the installation from other software.

   colander

    Library for schema creation. Used with :term:`deform` to create the forms within VoteIT.
    See `<http://docs.pylonsproject.org/projects/colander/en/latest>`_ for documentation.

   deform

    Form generation libraty. Handles all forms within VoteIT.
    See `<http://docs.pylonsproject.org/projects/deform/en/latest>`_ for documentation and
    `<http://deformdemo.repoze.org>`_ for demo and examples.

   Event

    Part of the :term:`Zope Component Architechture`.
    A class that signals that something has happend. Used by a :term:`subscriber`.
    Short intro at: :ref:`events`.

   Fanstatic

    Publishing package ment to handle static resources like javascript and css. It makes it a lot easier
    to handle updates and versioning + bundling of resources. Documentation at:
    `<http://www.fanstatic.org>`_

   git

    Source control system. Available at: `<http://git-scm.com>`_

   Pyramid
   
    The web framework VoteIT is built on. Check out the great documentation at:
    `<http://docs.pylonsproject.org>`_

   virtualenv

     Package to create an isolated Python environment.

   Paste

    Python WSGI deployment and development system. We normally use the HTTP server that's
    contained within this package, but any WSGI server could be used. `<http://pythonpaste.org>`_

   Python

    Programming language that VoteIT is written in. See `<http://www.python.org>`_

   setuptools

    Python package handler. See `<http://packages.python.org/an_example_pypi_project/setuptools.html`>_
    for an introduction.

   Subscriber

    Part of the :term:`Zope Component Architechture`.
    Subscribes to events and acts upon them. One of the plug points in VoteIT where
    you can inject functionality.
    Short intro at: :ref:`subscribers`.

   Utility

    Part of the :term:`Zope Component Architechture`.
    A short intro is available at: :ref:`utilities`.

   ZODB

    An object oriented database. Makes persistence very easy to implement with objects.
    Since we're using an object oriented language, it also makes sense to store objects as objects,
    rather than using an SQL mapper. See `<http://www.zodb.org>`_

   Zope Component Architechture

    A framework for Python development to make code more reusable and understandable.
    There's a short introduction available within the VoteIT docs: :ref:`zca`.
    A more comprehensive and general one: `<http://www.muthukadan.net/docs/zca.html>`_

