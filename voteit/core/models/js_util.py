import re

from zope.interface import implements
from pyramid.i18n import TranslationString

from voteit.core.models.interfaces import IJSUtil


MSGID_PATTERN = re.compile(r'^[a-zA-Z0-9_]{2,50}$')


class JSUtil(object):
    """ Handle translations that javascripts might need.
        See :mod:`voteit.core.models.interfaces.IJSUtil`.
    """
    implements(IJSUtil)

    def __init__(self):
        self.translations = {}

    def add_translations(self, *tstrings):
        for ts in tstrings:
            if not isinstance(ts, TranslationString):
                raise TypeError("Must be a pyramid.i18n.TranslationString")
            if ts.domain is None:
                raise ValueError("The translation string '%s' lacks a translation domain" % ts)
            if not MSGID_PATTERN.match(ts):
                raise ValueError("'%s' is an unsuitable msgid to be included in javascript." % ts)
            #This will make the key the message id, not the whole object
            self.translations[unicode(ts)] = ts

    def get_translations(self):
        return self.translations.copy()


def includeme(config):
    """ Register utility. This method is used when you include this
        module with a Pyramid configurator. This specific module
        will be included as default by VoteIT.
    """
    config.registry.registerUtility(JSUtil(), IJSUtil)
