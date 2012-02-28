#!/usr/bin/python

import htmltruncate
import unittest

class TruncateTest(unittest.TestCase):
    cases = ( ('this <b>word</b> is bolded', 4, "this"),
              ('this <b>word</b> is bolded', 6, "this <b>w</b>"),
              ('this <b>word</b> is bolded', 8, "this <b>wor</b>"),
              ('this <b>word</b> is bolded', 10, "this <b>word</b> "),
              ('this <b>word</b> is bolded', 700, "this <b>word</b> is bolded"),
              ('the second tag <span class="hello">is closed, but is the <a href="/test.html">first one</a> closed too?</span>', 52,
               'the second tag <span class="hello">is closed, but is the <a href="/test.html">first one</a> close</span>'),
              ("This is a test of the truncating feature in EDCZ&trade; please use with caution.", 65,
               "This is a test of the truncating feature in EDCZ&trade; please use with"),
              ("<p>Well here's another test of truncation <span>with</span> a little bit o markup and a bunch more stuff</p>", 65,
               "<p>Well here's another test of truncation <span>with</span> a little bit o markup</p>"),
              ("This is a test of the truncating feature in EDCZ&trade; please <span>use</span> with caution.", 65,
               "This is a test of the truncating feature in EDCZ&trade; please <span>use</span> with"),
              ("This is a test of the truncating features in EDCZ please use <span>with</span> caution <span>more with</span>.", 65,
               "This is a test of the truncating features in EDCZ please use <span>with</span>"),
              ("This is a test of the truncating features in EDCZ please use <span>with caution</span>", 65,
               "This is a test of the truncating features in EDCZ please use <span>with</span>"),
              ("<span>This</span> is a test of the truncating features in EDCZ please use <span>with caution</span>", 65,
               "<span>This</span> is a test of the truncating features in EDCZ please use <span>with</span>"),
              ("And this baby right here is the special last line that get's chopped a little shorter", 55,
               "And this baby right here is the special last line that ") )

    def testTruncation(self):
        for input, count, output in self.cases:
            self.assertEqual( htmltruncate.truncate(input, count), output )

    def testUnbalanced(self):
        self.assertEqual( htmltruncate.truncate( 'I am a <b>bad</strong> little string with unbalanced tags', 20 ), htmltruncate.ERR_UNBALANCED )

    def testEntity(self):
        self.assertEqual( htmltruncate.truncate( "I&apos;m one", 3 ), "I&apos;m" )

    def testSelfClosing(self):
        self.assertEqual( htmltruncate.truncate( "I need<br /> a break", 11 ), "I need<br /> a br" )

    def testEllipsis(self):
        self.assertEqual( htmltruncate.truncate('this <b>word</b> is bolded', 10, '...' ), "this <b>word</b> ...")

if __name__ == "__main__":
    unittest.main()
