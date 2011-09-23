import os
import sys

from pyramid.view import view_config
from pyramid.decorator import reify

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.security import MANAGE_SERVER


class LogsView(BaseView):
    
    @reify
    def _logdir(self):
        #FIXME: Rewrite when logging is read from the paster conf files
        me = sys.argv[0]
        me = os.path.abspath(me)        
        buildoutpath = os.path.dirname(os.path.dirname(me))
        rel = os.path.join(buildoutpath, 'var', 'log')
        return os.path.abspath(os.path.normpath(rel))
    
    @reify
    def logfile_ids(self):
        return [x for x in os.listdir(self._logdir) if x.endswith('.log')]
    
    @view_config(name="server_logs", context=ISiteRoot, permission=MANAGE_SERVER, renderer="templates/server_logs.pt")
    def log_view(self):
        """ Choose a log and display + format its content. """
        
        #Load log?
        file = self.request.GET.get('file', None)
        logdata = None
        if file in self.logfile_ids:
            #Formatting?
            filepath = os.path.join(self._logdir, file)
            with open(filepath, 'r') as f:
                #Perhaps we should format it in a nicer way
                logdata = f.read()
        
        self.response['logfiles'] = self.logfile_ids
        self.response['current_log'] = file
        self.response['logdata'] = logdata
        return self.response