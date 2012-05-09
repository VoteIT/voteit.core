Installing
==========


Requirements
------------

* Python 2.6 or 2.7. (Might work with others, but don't use lower than 2.6)
* a POSIX-compatible operating system. As far as we know, all Linux / UNIX
  version work, including Mac Os X. Windows might work as well, but we haven't
  tested it and we wouldn't recommend deploying it on Windows servers for security reasons.
* Setuptools for Python installed. If you can type "easy_install" in a
  terminal, you have it.
* Virtualenv for Python. (Installed with "easy_install virtualenv" as root.
  See `<http://www.virtualenv.org>`_ for more information)

See the :term:`Pyramid` docs on installation if you need help. VoteIT requires the same things.

Creating an isolated Python enviroment
--------------------------------------

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
        voteit.core
    
    #Which eggs should be downloaded? You can list other plugins you want to use here.
    eggs =
        voteit.core
    
    #See the buldout docs for more info on these options
    newest = false
    prefer-final = true
    eggs-directory = ${buildout:directory}/eggs
    versions = versions
    
    [voteit.core]
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
    #Uncomment the line below to make buildout pick Pyramid 1.2.1
    #Pyramid = 1.2.1

Read the :term:`Buildout` docs for more info on configuration options.

You also need to download a version of bootstrap.py.
It's usually available in buildout configs, but you can download it
from Zope directly if you want to: `<http://svn.zope.org/zc.buildout/trunk/bootstrap>`_

Create a directory and put the two files in that dir

Now let's install  a :term:`virtualenv` in that directory. Run the following
while inside that directory. Pick python version 2.6 or 2.7

   .. code-block:: text

    virtualenv . -ppython2.7 --no-site-packages

Now run bootstrap with the local Python.

   .. code-block:: text

    bin/python2.7 bootstrap.py

If it worked as expected, a new file called buildout should exist in the bin-directory.
Run it to start the buildout process.

   .. code-block:: text

    bin/buildout

This should install all packages needed to run a default VoteIT installation.
