.. _glossary:

Glossary
========

.. glossary::
   :sorted:

   Buildout

    `Buildout <http://www.buildout.org>`_ is a Python-based build system for creating, assembling and deploying applications
    from multiple parts, some of which may be non-Python-based. It lets you create a buildout
    configuration and reproduce the same software later.

    By using it, you don't have to care about a specific package or dependency beeing available
    on your platform. It also isolates the installation from other software.

   Fanstatic

    Publishing package ment to handle static resources like javascript and css. It makes it a lot easier
    to handle updates and versioning + bundling of resources. Documentation at:
    `<http://www.fanstatic.org>`_


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

   ZODB

    An object oriented database. Makes persistence very easy to implement with objects.
    Since we're using an object oriented language, it also makes sense to store objects as objects,
    rather than using an SQL mapper. See `<http://www.zodb.org>`_


