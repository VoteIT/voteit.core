Installing
==========


Requirements
------------

* Python 2.7 - it will probably work on 2.6 aswell, but no lower version is compatible with :term:`Pyramid`.
* a POSIX-compatible operating system. As far as we know, all Linux / UNIX
  version work, including Mac OS X. Windows might work as well, but we haven't
  tested it and we wouldn't recommend deploying it on Windows servers for security reasons.
* :term:`Setuptools` for Python installed. If you can type "easy_install" in a
  terminal, you have it.
* :term:`Virtualenv` for Python. (Installed with ``easy_install virtualenv`` as root.
  See `<http://www.virtualenv.org>`_ for more information)

See the :term:`Pyramid` docs on installation if you need help. VoteIT requires the same things.

Use a Python via :term:`virtualenv`!
------------------------------------

If you don't, you might mess up the system Python on your computer. A lot of programs might depend on that, so it's a pretty bad idea.

Create a directory and add a Python to it

   .. code-block:: bash

    mkdir my_test
    cd my_test
    virtualenv . -ppython2.7


Installing via :term:`buildout`
-------------------------------

A barebone :term:`Buildout` environment consists of a bootstrap.py file and
a buildout.cfg file.

Some example configurations:

* `VoteIT core development - used for developing VoteIT <https://github.com/VoteIT/voteit_devel_buildout>`_
* `Production buildout for mote.voteit.se <https://github.com/VoteIT/mote_voteit_buildout>`_

You can of course create the buildout.cfg file from scrach yourself.
These are the required components.

   .. code-block:: text

    [buildout]
    #parts sets which sections to include
    parts =
        VoteIT
    
    #Which eggs should be downloaded? You can list other plugins you want to use here.
    #waitress is a webserver
    eggs =
        voteit.core
        waitress
    
    #See the buildout docs for more info on these options
    newest = false
    prefer-final = true
    eggs-directory = ${buildout:directory}/eggs
    versions = versions

    extensions =
        mr.developer
    
    # mr.developer settings:
    sources = sources
    auto-checkout = *

    [VoteIT]
    #This section defines the installation of voteit.core
    recipe = zc.recipe.egg
    dependent-scripts = true
    unzip = true
    #The ${buildout:eggs} var is a reference to eggs in the [buildout] section
    eggs =
        ${buildout:eggs}
    interpreter = py
    
    [versions]
    #If you want to force a specific version of something, you can add it here.
    #Uncomment the line below to make buildout pick Pyramid 1.4.5 for instance
    #Pyramid = 1.4.5

    [sources]
    #Uncomment the line below to check out the development version of voteit.core
    #You can add any plugins you want to develop yourself here.
    #voteit.core = git git@github.com:VoteIT/voteit.core.git

Read the :term:`Buildout` docs for more info on configuration options.

You also need to download a version of bootstrap.py.
It's usually available in buildout configs, but you can download it
from Zope directly if you want to: `<http://downloads.buildout.org/2/bootstrap.py>`_

Create a directory and put the two files in that dir

Now run bootstrap with the local Python.

   .. code-block:: bash

    bin/python2.7 bootstrap.py

If it worked as expected, a new file called buildout should exist in the bin-directory.
Run it to start the buildout process.

   .. code-block:: bash

    bin/buildout

This should install all packages needed to run a default VoteIT installation.

Alternative version: Installing via :term:`pip`
-----------------------------------------------

There's a ``requirements.txt`` file in ``voteit.core``.
Run ``pip install -r requirements.txt`` to fetch the correct versions of all dependencies.
