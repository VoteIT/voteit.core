Poll Plugin
===========

.. note::

    You should be familiar with :ref:`development_environment` and :ref:`basic_plugin`
    before you try this out.

.. warning::

    This tutorial is outdated and needs an update!


Poll plugins are responsible for a large portion of the voting process. They calculate the result,
provide data so a vote form can be created and they display the result. If you want to implement
a specific polling method, this is what you'll want to write.


.. tip::

    Rather learn by example? There are several poll plugins available:

    * `Schulze STV / PR <https://github.com/VoteIT/voteit.schulze>`_
    * `Combined simple <https://github.com/VoteIT/voteit.combined_simple>`_
    * `Dutt <https://github.com/VoteIT/voteit.dutt>`_
    * Majority Poll is an example that comes with the VoteIT source: :mod:`voteit.core.plugins.majority_poll`


The poll layout
---------------

This is the basic structure of polls. Each poll also has a reference to the
proposals that participate in each poll. Proposals can be referenced by several
polls.

When users vote, their votes will be added inside the polls. Each vote will have the
same name as the userid of the one who added it.

 * Agenda Item

   * Proposal 1

   * Proposal 2

   * Poll 1

     * Vote 1
     * Vote 2
     * Vote 3

   * Poll 2

     * Vote 1
     * Vote 2


Creating the package
--------------------

  .. note::

    If you'd like to download the example from this tutorial, it's available here:
    :download:`demo_poll.tgz <../files/demo_poll.tgz>`.

From within the buildout directory, go to the ``src`` folder and create a new package using Pyramid scaffolds.
Follow the instructions from :ref:`basic_plugin`.

We'll use the project name ``demo_poll`` for this tutorial.

Remove any example content in ``demo_poll/demo_poll``.

Now register the package in buildout and your paster.ini file as described in :ref:`basic_plugin`.


An example poll method
----------------------

Let's create a new poll method. It will have the following functions:

 * You only get to pick one choice with a radio button.
 * When the poll closes, a winner is picked randomly among all the votes.
 * This poll method might not be the best for real polls, but it's equally
   bad to any poll using a majority vote with more than 2 alternatives. :)


Writing the plugin
------------------

A poll plugin is by design an :term:`adapter`. It's built to adapt a Poll. To work correctly,
it needs to implement the :mod:`voteit.core.models.interfaces.IPollPlugin` interface, and it
needs to be registered as an adapter.

All of the important attributes and methods of a class are always documented in the interface
of that class. If you want to read more about something, check the interface documentation.

Create ``models.py``

  .. code-block :: py

    class RandomPollPlugin(PollPlugin):
        """ A custom poll plugin that randomly picks a winner among the votes. """
    
        name = 'RandomPollPlugin'
        title = _(u'Random poll method')
        description = _(u"Picks a winning vote randomly from the recieved ones.")


Initial test code
-----------------

To make sure things work as expected, we need to write some tests too.
Change the file ``tests.py`` to reflect the new code update. It should look something like this:

  .. code-block :: py

    import unittest

    from pyramid import testing
    from zope.interface.verify import verifyClass
    from zope.interface.verify import verifyObject
    from voteit.core.models.interfaces import IPollPlugin
    
    
    class RandomPollPluginTests(unittest.TestCase):
        def setUp(self):
           self.config = testing.setUp()
        
        def tearDown(self):
           testing.tearDown()
        
        @property
        def _cut(self):
           """ Return the Class Under Test.
               This is a property so you can instantiate it directly if you want to.
           """
           from demo_poll.models import RandomPollPlugin
           return RandomPollPlugin

        def test_verify_class(self):
            self.failUnless(verifyClass(IPollPlugin, self._cut))
        
        def test_verify_object(self):
            context = testing.DummyModel()
            self.failUnless(verifyObject(IPollPlugin, self._cut(context)))

For the basics of testing, see the Pyramid documentation.
The test above will make sure that the interface is implemented correcly. Otherwise it will produce
errors that explains what went wrong. We'll add more functions to the testing code later.

To run the test, use ``nosetests`` in ``bin``.

  .. code-block :: bash

    ./bin/nosetests src/demo_poll


Registering an adapter
----------------------

The plugin needs to be registered as an :term:`adapter` to work. This is normally done during application
startup in the method ``includeme``. Open ``__init__.py`` and add our plugin there.

  .. code-block :: py

    def includeme(config):
        from voteit.core.models.interfaces import IPoll
        from voteit.core.models.interfaces import IPollPlugin
    
        from demo_poll.models import RandomPollPluginTests
        
        config.registry.registerAdapter(RandomPollPluginTests, #The class the adapter will be implemented from
                                        (IPoll,), #Which kind of objects is this adapter for?
                                        IPollPlugin, #Interface this adapter implements
                                        name = RandomPollPluginTests.name) #Name of the adapter.

To make sure the adapter is registered as expected, we have to write an integration test.
Add the following lines to ``tests.py``

  .. code-block :: py

    def test_integration(self):
        from voteit.core.models.poll import Poll
        self.config.include('demo_poll') #Will run includeme
        qa = self.config.registry.queryAdapter
        poll = Poll()
        self.failUnless(qa(poll, IPollPlugin, name = 'RandomPollPlugin'))

 * When ``self.config.include('demo_poll')`` is run, it will execute the function ``includeme``.
 * ``queryAdapter`` will return the adapter or ``None`` if no adapter can be found.

If everything worked as expected, 3 tests should now pass.


Test fixture
------------

Before we write more complex functions, we need to create a test fixture.
The purpose of this is to mimic a real environment, so we can test high level
functions.

This code will create the neccessary poll fixture. We'll add some extra components
from VoteIT to be able to run all poll tests.

Add this method to the test class in ``tests.py``:

  .. code-block :: py

    def _fixture(self):
        from voteit.core.testing_helpers import active_poll_fixture
        root = active_poll_fixture(self.config)
        ai = root['meeting']['ai']
        return ai

The above code will register needed components, create an app root, a meeting,
an agenda item, one poll and two proposals.
See :func:`voteit.core.testing_helpers.active_poll_fixture` for more info.

For this test, we only need to care about the contents of the agenda item.
So the function can return that object.


The vote form - ``get_vote_schema``
-----------------------------------

The code in the example ``get_vote_schema`` produces a schema with a radio button choice.
It works as it is! If you want to read more about schemas, check the :term:`colander` documentation.

For testing, it might be a good idea to check that a ``colander.SchemaNode`` is
returned. The following code will do that.

  .. code-block :: py

    def test_get_vote_schema(self):
        from colander import SchemaNode
        ai = self._fixture()
        poll = ai['poll']
        obj = self._cut(poll)
        out = obj.get_vote_schema()
        self.assertIsInstance(out, SchemaNode)

It might also be a good idea to test properties of the returned schema,
but this is a basic example.


Settings form - ``get_settings_schema``
---------------------------------------

Our poll methods won't have any special settings, so the method ``get_settings_schema`` can be removed.
If you want to write one, check the interface for specifications. The package ``voteit.schulze`` uses
settings, you can also read that code for an example.


Producing a result - ``handle_close``
-------------------------------------

Next up is ``handle_close``. It's called when the poll is closed, and should do any kind of calculation
to produce a result from a poll.

First, let's add an import to the top of the file:

  .. code-block :: py

    from random import choice
    #Choice simply picks one random alternative from a sequence.

Next, let's write the code for the funciton. There are two ways to access votes,
either simply find all the votes within the poll context, or use the ``ballots`` attribute
of the poll.

We'll simply fetch all the votes.

  .. code-block :: py

    def handle_close(self):
        #self.context here is the poll object
        votes = self.context.get_content(content_type = 'Vote')
        if not votes:
            raise ValueError("Need at least one vote")
        #Note that this will cause an error if no votes exist.
        winner_vote = choice(votes)
        winner_uid = winner_vote.get_vote_data()['proposal']
        result = dict(
            winner = winner_uid,
            total_votes = len(votes),
        )
        #The result must be stored in the attribute poll_result.
        self.context.poll_result = result

 * ``self.context`` is always the poll object. It's the only valid object to adapt for a
   poll plugin.
 * ``get_content`` will return all the votes in this context.
 * ``choice`` will simply pick one of them from the list. If the list is empty,
   it will raise an exception
 * ``poll_result`` attribute on a poll is where the result should be stored by convention.

  .. warning::

    When dealing with ballots or votes, make sure you don't modify them.
    Use the function ``copy.deepcopy`` if you need to alter objects,
    to make sure you don't touch the original!

Testing code that contains random might be a bit hard, but we can cheat.
We'll simply add just one vote to make sure who's the winner.

Extend the test class in ``tests.py`` with the following:

  .. code-block :: py

    def test_handle_close(self):
        from voteit.core.models.vote import Vote
        ai = self._fixture()
        poll = ai['poll']
        poll['vote'] = Vote()
        poll['vote'].set_vote_data({'proposal': ai['prop1'].uid})
        obj = self._cut(poll)
        obj.handle_close()
        self.assertEqual(obj.context.poll_result['winner'], ai['prop1'].uid)
        self.assertEqual(obj.context.poll_result['winner'], poll['vote'].get_vote_data()['proposal'])
        self.assertEqual(obj.context.poll_result['total_votes'], 1)


Presenting the result - ``render_result``
-----------------------------------------

Since we'll only have one winner with this plugin, we can change the
code for render result a bit.

  .. code-block :: py

    def render_result(self, request, api, complete=True):
        winner = self.context.get_proposal_by_uid(self.context.poll_result['winner'])
        response = dict(
            total_votes = self.context.poll_result['total_votes'],
            winner = winner,
        )
        return render('result.pt', response, request = request)

 * ``get_proposal_by_uid`` simply fetches a proposal object with the corresponding uid.
 * All of the things passed along in the respone dict will be available under the same name
   in the template.

Let's change the template as well.

  .. code-block :: html

    <tal:main xmlns:i18n="http://xml.zope.org/namespaces/i18n" i18n:domain="demo_poll">
        <h1 i18n:translate="">Poll result</h1>
        <strong i18n:translate="">Winner</strong>
        <div><a href="${request.resource_url(winner)}">${winner.title}</a></div>
        <strong i18n:translate="">Number of votes</strong>
        <div>${total_votes}</div>
    </tal:main>

Finally, we need to make sure the template renders as expected by writing a test for it.

  .. code-block :: py

    def test_render_result(self):
        from voteit.core.models.vote import Vote
        from voteit.core.views.api import APIView
        request = testing.DummyRequest()
        ai = self._fixture()
        poll = ai['poll']
        api = APIView(poll, request)
        poll['vote'] = Vote()
        poll['vote'].set_vote_data({'proposal': ai['prop1'].uid})
        obj = self._cut(poll)
        obj.handle_close()
        out = obj.render_result(request, api)
        self.assertIn('http://example.com/meeting/ai/prop1/', out)

The test is almost equal to the previous one, but instead we check the generated output.
Testing urls always start with ``http://example.com``.


Enabling the new plugin
-----------------------

Live testing is of course the most important part.
You've already added ``demo_poll`` to ``buildout.cfg``. You also need to add it
to the paster ini file, located at ``etc/development.ini`` if you've used VoteITs
dev environment, if you haven't done so already.

Start the server:

  .. code-block :: py

    ./bin/pserve etc/development.ini

Create a meeting, and enable our poll plugin in ``meeting poll settings`` in
the ``settings`` menu. (Make sure ``random poll method`` is checked)

Now you should be able to use the poll method within an agenda item.
