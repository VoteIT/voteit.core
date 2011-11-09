from pyramid.scaffolds import PyramidTemplate
from paste.util.template import paste_script_template_renderer


class PollPluginTemplate(PyramidTemplate):
    _template_dir = 'poll_plugin'
    summary = 'VoteIT Poll Plugin'
    template_renderer = staticmethod(paste_script_template_renderer)
