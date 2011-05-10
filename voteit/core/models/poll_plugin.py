from zope.interface import implements
from voteit.core.models.interfaces import IPollPlugin


class PollPlugin(object):
    """ Base class for poll plugins. Subclass this to make your own. """
    implements(IPollPlugin)
    
    @property
    def name(self):
        raise NotImplementedError("'name' must be a property on the subclass.")

    @property
    def title(self):
        raise NotImplementedError("'title' must be a property on the subclass.")
    
    def get_vote_schema(poll):
        """ See IPollPlugin """
        raise NotImplementedError("'get_vote_schema' must be implemented by subclass.")
    
    def get_vote_class():
        """ See IPollPlugin """
        raise NotImplementedError("'get_vote_class' must be implemented by subclass.")
        
    def get_settings_schema(poll):
        """ See IPollPlugin """
        raise NotImplementedError("'get_settings_schema' must be implemented by subclass.")

    def render_result(poll, ballots):
        """ See IPollPlugin """
        raise NotImplementedError("'render_result' must be implemented by subclass.")
