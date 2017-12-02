# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IDiffText


class DiffTextTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.diff_text import DiffText
        return DiffText

    def test_verify_class(self):
        self.failUnless(verifyClass(IDiffText, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IDiffText, self._cut(testing.DummyModel())))

    def test_get_paragraphs_zoe(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _ZOE
        result = obj.get_paragraphs()
        self.assertEqual(len(result), 11)
        expected_6 = """I want someone who has been in love and been hurt,
who respects sex, who has made mistakes and learned from them."""
        self.assertEqual(result[5], expected_6)

    def test_get_paragraphs_boye(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _BOYE
        result = obj.get_paragraphs()
        self.assertEqual(len(result), 2)
        expected = ["Det gör mycket mer ont när våren inte kommer alls.", "Det är ok om den tvekar."]
        self.assertEqual(result, expected)

    def test_no_diff_zoe(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _ZOE
        paragraphs = obj.get_paragraphs()
        expected_6 = """I want someone who has been in love and been hurt,
who respects sex, who has made mistakes and learned from them."""
        results = obj(paragraphs[5], expected_6)
        self.assertEqual(expected_6, results)

    def test_diff_with_lines_zoe(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _ZOE
        paragraphs = obj.get_paragraphs()
        changed = """Who respects sex,\nwho has made mistakes and learned from them!"""
        results = obj(paragraphs[5], changed)
        expected = u'<strong><s class="text-danger">I want someone who has been in love and been hurt,\n' \
                   u'who respects sex, who has made mistakes and learned from them.</s></strong>\n' \
                   u'<strong class="text-success">Who respects sex,\n' \
                   u'who has made mistakes and learned from them!</strong>'
        self.assertEqual(expected, results)


#Note that the sometimes odd spaces in the texts inserted for the tests :)
_ZOE = """

I want a dyke for president.

I want a person with AIDS for president and I want a fag for vice president 
and I want someone with no health insurance and I want someone who grew up in a 
place where the earth is so saturated with toxic waste that 
they didn’t have a choice about getting leukemia.

I want a president that had an abortion at sixteen and I want a candidate 
who isn’t the lesser of two evils and I want a president who lost their last lover to AIDS, 
who still sees that in their eyes every time they lay down to rest, who held their lover 
in their arms and knew they were dying.



I want a president with no air-conditioning, 
a president who has stood in line at the clinic, at the DMV, at the welfare office, 
and has been unemployed and laid off and sexually harassed and gaybashed and deported.

I want someone who has spent the night in the tombs and had a cross burned on their lawn 
and survived rape.

I want someone who has been in love and been hurt,        
who respects sex, who has made mistakes and learned from them. 

I want a Black woman for president.

I want someone with bad teeth and an attitude, 
someone who has eaten that nasty hospital food, someone who crossdresses and has 
done drugs and been in therapy.

I want someone who has committed civil disobedience. 

And I want to know why this isn’t possible. I want to know why we started learning 
somewhere down the line that a president is always a clown. Always a john and never a hooker. 
Always a boss and never a worker. Always a liar, always a thief, and never caught.


― Zoe Leonard
"""


_BOYE = "Det gör mycket mer ont när våren inte kommer alls.\n   \n  Det är ok om den tvekar."