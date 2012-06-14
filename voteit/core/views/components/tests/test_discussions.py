# -*- coding:utf-8 -*-

import unittest

from pyramid import testing


class DiscussionsComponentTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def test_truncate_long(self):
        
        text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
               u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
               u"consectetur adipiscing elit. In hac habitasse platea dictumst. " \
               u"Sed sit amet tortor at nisl malesuada tristique. Nulla faucibus " \
               u"egestas felis, at ullamcorper arcu sollicitudin amet."
                
        truncated_text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
                         u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
                         u"consectetur adipiscing elit. In hac habitasse platea dictumst. " \
                         u"Sed sit amet tortor at nisl malesuada tristique. Nulla fa…"

        from voteit.core.views.components.discussions import truncate
        
        self.assertEqual(truncate(text, 240), (truncated_text, True))
        
    def test_truncate_short(self):
        
        text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
               u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
               u"consectetur adipiscing elit. In hac habitasse platea dictumst."
                
        truncated_text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
                         u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
                         u"consectetur adipiscing elit. In hac habitasse platea dictumst."

        from voteit.core.views.components.discussions import truncate
        
        self.assertEqual(truncate(text, 240), (truncated_text, False))
        
    def test_truncate_no_length(self):
        
        text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
               u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
               u"consectetur adipiscing elit. In hac habitasse platea dictumst."
                
        truncated_text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
                         u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
                         u"consectetur adipiscing elit. In hac habitasse platea dictumst."

        from voteit.core.views.components.discussions import truncate
        
        self.assertEqual(truncate(text, None), (truncated_text, False))