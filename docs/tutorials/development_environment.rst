.. _development_environment:

Setting up a development environment
====================================

This tutorial is for UNIX/Linux operating systems. We don't recommend
doing development on a windows machine, although it is possible. (If you'd like to contribute
a guide about that, feel free!)

Checklist
---------

 * Make sure you have Python 2.7 installed. If not, consult the :term:`Python`
   or :term:`Pyramid` docs for installation instructions.
 * You need a C-compiler, like GCC installed. On some Linux systems, there's a bundle called
   ``build-essential`` that you can install. On macs, you need ``XCode``. (Some components are
   written in C-code) Typing ``gcc`` in a terminal should produce some result if you have it.
 * We use :term:`git` as source control, but it's only needed in this example.
 * You need some kind of editor. We use `Aptana <http://www.aptana.com>`_ but you can use anything
   you like.
 * :term:`Setuptools` should be installed, if you can type ``easy_install`` you have it.
 * :term:`virtualenv` is highly recommended. Typing ``easy_install virtualenv`` as root should
   install it.


Using VoteITs development buildout
----------------------------------

Rather than creating your own :term:`buildout` configuration, you can use VoteITs for your projects
too if you like. It works for core development as well as plugin development.

First, let's clone the repository with git:

.. code-block :: bash

   git clone git://github.com/VoteIT/voteit_devel_buildout

Go into the directory. Inside you'll find the buildout configuration in the file ``buildout.cfg``.

Now run :term:`virtualenv` to create an isolated python environment. Make sure you have python2.7 installed first,
and that it's accessable in your system path!

.. code-block :: bash

   virtualenv . --ppython2.7

Inside the ``bin``-dir you should find a python executable now. To start the buildout process, run ``bootstrap.py``
with it. Do mind the search path, otherwise you might use the wrong Python installation!

.. code-block :: bash

   ./bin/python bootstrap.py

Now we're ready to run buildout. It will download and install all required packages in the folder we just created.
Some packages will have to be compiled too.

.. code-block :: bash

   ./bin/buildout

This will take a while, go and make some coffee...


Starting the server
-------------------

When buildout finishes, you should be able to start the regular development server.

.. code-block :: bash

   ./bin/pserve etc/development.ini

If everything worked as expected, you should now have a server up and running on the port specified.

If you want to develop your own plugin and add it to the configuration, see :ref:`basic_plugin`
