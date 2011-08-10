import os

from zope.interface import implements
from BTrees.OOBTree import OOBTree

from voteit.core.models.interfaces import IHelpUtil


class HelpUtil(object):
    """ Manages help pages.
        See IHelpUtil for more info
    """
    implements(IHelpUtil)

    def __init__(self, locale='en'):
        self.set_default_locale(locale)
        self._helpdata = OOBTree()

    def set_default_locale(self, locale):
        self.locale = locale

    def add_help_file(self, id, path, locale=None):
        text = open(path).read()
        self.add_help_text(id, text, locale=locale)

    def add_help_text(self, id, text, locale=None):
        if locale is None:
            locale = self.locale
        if not locale in self._helpdata:
            self._helpdata[locale] = OOBTree()
        self._helpdata[locale][id] = text

    def get(self, id, locale=None):
        if not locale:
            locale = self.locale
        if not locale in self._helpdata:
            return None
        return self._helpdata[locale].get(id)
        