Poll Plugin
===========

  .. note::

    You should be familiar with :ref:`development_environment` and :ref:`basic_plugin`
    before you try this out.

Poll plugins are responsible for a large portion of the voting process. They calculate the result,
provide data so a vote form can be created and they display the result. If you want to implement
a specific polling method, this is what you'll want to write.

For this tutorial, we'll assume that your using VoteITs development buildout.
(Again, see the :ref:`development_environment` for information on how to set that up.)

From within the buildout directory, go to the ``src`` folder and create a new package using paster.
VoteIT provides a skeleton for creating poll plugins called ``voteit_poll_plugin``.

  .. code-block :: bash

    ../bin/paster create -t voteit_poll_plugin

We'll use the project name ``demo_poll`` for this tutorial.

If you go into the package, you'll find setup.py and setup.cfg + some readme files. You might
want to take a look at these if you plan to release the package publicly.

You'll also find another folder called ``demo_poll``. This is where all the relevant code is.
By default, an example poll plugin will be shipped with this package. If you're more into
playing with the code than reading manuals - this is where you stop reading :)

FIXME: To be continued...
