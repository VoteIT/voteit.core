# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IDiffText


class DiffTextTests(unittest.TestCase):
    maxDiff = None

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
        expected = 'I want someone who has been in love and been hurt, <br/> who respects sex, who has made mistakes ' \
                   'and learned from them.'
        results = obj(paragraphs[5], expected)
        self.assertEqual(expected, results)

    def test_diff_with_lines_zoe(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _ZOE
        paragraphs = obj.get_paragraphs()
        changed = """Who respects sex, who has made mistakes and learned from them!"""
        results = obj(paragraphs[5], changed)
        expected = '<span class="text-diff-removed">I want someone who has been in love and been hurt, <br/> ' \
                   'who</span> <span class="text-diff-added">Who</span> respects sex, ' \
                   'who has made mistakes and learned from <span class="text-diff-removed">them.</span> ' \
                   '<span class="text-diff-added">them!</span>'
        self.assertEqual(expected, results)

    def test_diff_with_bullets(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _JOHNNY
        paragraphs = obj.get_paragraphs()
        changed = """Det här är en punktlista
• En grej
• En mellangrej"""
        results = obj(paragraphs[0], changed)
        expected = """Det här är en punktlista
• En grej
<span class="text-diff-removed">• Ytterligare en grej</span>
<span class="text-diff-added">• En mellangrej</span>"""
        self.assertEqual(expected, results)

    def test_diff_with_other_bullets(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _JOHNNY
        paragraphs = obj.get_paragraphs()
        changed = """Det här är också en punktlista
- En grej
- En mellangrej"""
        results = obj(paragraphs[1], changed)
        expected = """Det här är också en punktlista
- En grej
<span class="text-diff-removed">- Ytterligare en grej</span>
<span class="text-diff-added">- En mellangrej</span>"""
        self.assertEqual(expected, results)

    def test_diff_with_no_bullets(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        obj.text = _JOHNNY
        paragraphs = obj.get_paragraphs()
        changed = """Det här är inte en punktlista
Det är bara ett ovanligt stycke"""
        results = obj(paragraphs[2], changed)
        expected = """Det här är inte en punktlista <br/> Det är bara ett <span class="text-diff-removed">vanligt</span> <span class="text-diff-added">ovanligt</span> stycke"""
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

_JOHNNY = """Det här är en punktlista
• En grej
• Ytterligare en grej

Det här är också en punktlista
- En grej
- Ytterligare en grej

Det här är inte en punktlista
Det är bara ett vanligt stycke"""