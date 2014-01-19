Simple configuration for testing
================================

VotIT needs a :term:`Paste` .ini file to run. It defines which applications to load
by the server, and settings for the different apps. This is also where you enable or
disable plugins.

Add the following to the root of your :term:`Buildout` directory. (Comments within the code)

.. warning::

    Don't use this as a production environment - this is for development and testing only!
    If an error occurs, anyone viewing the page may execute any code they like.
    For production config, see :ref:`deploying`.

.. code-block:: text

    [app:VoteIT]
    use = egg:voteit.core
    
    #Pyramid defaults - check pyramid docs for explanation of these
    pyramid.reload_templates = true
    pyramid.debug_authorization = false
    pyramid.debug_notfound = false
    pyramid.debug_routematch = false
    pyramid.debug_templates = true
    #Add any extra packages here
    pyramid.includes =
        pyramid_debugtoolbar
        pyramid_zodbconn
        pyramid_tm
        voteit.core.tests.printing_mailer
        betahaus.viewcomponent.debug_panel
    
    #Transaction manager config for package: pyramid_tm
    tm.attempts = 3
    tm.commit_veto = pyramid_tm.default_commit_veto
    #ZODB config for package: pyramid_zodbconn - location of Data.fs file
    zodbconn.uri = file://%(here)s/Data.fs?connection_cache_size=20000
    
    #VoteIT settings
    #Which language to use
    default_locale_name = sv
    #Not supported yet
    available_languages = en sv
    #Which timezone use - it's important to set this correctly!
    default_timezone_name = Europe/Stockholm
    #Salt for hashed login sessions. Set this to anything, just not the line below!
    tkt_secret = change me to whatever!
    #Caching
    cache_ttl_seconds = 3600
    
    #List any extra plugins you'll want to use here - these are loaded after VoteIT
    plugins = 
        voteit.core.plugins.majority_poll
    
    [pipeline:main]
    pipeline =
        fanstatic
        VoteIT
    
    [filter:fanstatic]
    use = egg:fanstatic#fanstatic
    bottom = True
    
    [server:main]
    use = egg:Paste#http
    host = 0.0.0.0
    port = 6543
    
    # Begin logging configuration
    [loggers]
    keys = root, voteit.core
    
    [handlers]
    keys = console
    
    [formatters]
    keys = generic
    
    [logger_root]
    level = INFO
    handlers = console
    
    [logger_voteit.core]
    level = DEBUG
    handlers =
    qualname = voteit.core
    
    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = NOTSET
    formatter = generic
    
    [formatter_generic]
    format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s
    
    # End logging configuration

Most of the options here are explained in the :term:`Pyramid` documentation.
Some are of special importance to VoteIT.

    pyramid.includes

        Anything listed here will be included before VoteIT. Since this is a development config
        we're including some debug tools.

    plugins

        Plugins to load after VoteIT. Anything listed here may override default options in VoteIT.
        If you want to add a plugin that tweaks aspects of VoteIT, this is the place.
        Normally, poll plugins are added here (like voteit.schulze package)

Save the file as `development.ini` and run the HTTP server this way:

.. code-block:: text

    bin/pserve serve development.ini

This should start a server on `localhost port 6543 <http://127.0.0.1:6543>`_.

To stop the server, press ctrl + c.

