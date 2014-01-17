.. _basic_plugin:

Writing a basic plugin
======================

  .. note::

    You need to have an installed development environment to do this. In case you haven't, see:
    :ref:`development_environment`

For the purpose of this tutorial, your package will be called ``demo_plugin``.

Go into your :term:`buildout` directory and runt the command ``bin/pcreate -t starter demo_plugin`` to create a
new package. You'll get some questions about your package - you can always change this information
later, but it's important to pick a suitable project name that reflects what the package should do.

Within the ``demo_plugin folder``, there's package information + a folder with the plugin code.
It will also be named ``demo_plugin`` and will probably contain a bit of sample code.

To make the plugin available in Python, you need to add it as a development package.
In ``buildout.cfg`` find the section ``[buildout]`` and add ``demo_plugin`` to the list of ``eggs``
+ add ``src/demo_plugin`` to the item ``develop``. Those two should look something like this:

  .. code-block :: text

    eggs =
        voteit.core
        coverage
        nose
        <etc...>
        demo_plugin

  .. code-block :: text

    develop =
        src/demo_plugin

.. tip::

    :term:`mr.developer` can handle development packages for you through :term:`buildout`.

To enable it, you need to rerun buildout:

  .. code-block :: bash

    ./bin/buildout

It should now be possible to import the new package from the interpeter ``py``. It's located in the ``bin``-folder.

  .. code-block :: bash

    ./bin/py

  .. code-block :: py

    >>> import demo_plugin
    >>>

:term:`Pyramid` (and VoteIT) uses a function called `ìncludeme`` as plug point.
It looks like this:

  .. code-block :: py

    def includeme(config):
        """ Do things with config like adding views or overiding things... """
        pass

This code will be executed whenever the following function is run with a configurator:

  .. code-block :: py

    config.include('demo_plugin')

Pyramid and VoteIT each has plug points within their paster configuration files. In the file used for
VoteIT core development, you'll probably find the following sections:

  .. code-block :: text

    pyramid.includes =
        pyramid_debugtoolbar
        pyramid_zodbconn
        pyramid_tm
        voteit.core.testing_helpers.printing_mailer
        betahaus.viewcomponent.debug_panel

  .. code-block :: text

    plugins = 
        voteit.core.plugins.majority_poll
        voteit.schulze
        voteit.dutt
        voteit.exportimport
        voteit.site
        voteit.statistics
        voteit.feed

The ``pyramid.include`` section is for core components that should be loaded *before* VoteIT.
The ``plugins`` section is for VoteIT plugins, or things that alter VoteIT. This section will
be loaded *after* VoteIT.

Normally you'll want to add things to the plugins section. If you add ``demo_plugin`` on a
new row here it will call the ``includeme`` function on startup.

See Pyramids documentation for information on what you can do with configurators. We'll also
provide a few examples for VoteIT-specific things.

