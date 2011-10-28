import os
import sys
import logging

from paste.deploy import loadapp
from pyramid.scripting import get_root

#FIXME: Need tests for scriptworker
#FIXME: Log file should be read the same way as if paster executed the server

class ScriptWorker(object):
    
    pidfile = None
    buildoutpath = None
    id = None
    root = None
    closer = None
    logger = None
    
    def __init__(self, id):
        """ Initialize worker.
            id will be part of the pid-file.
        """
        self.id = id

        #Buildout path
        me = sys.argv[0]
        me = os.path.abspath(me)        
        self.buildoutpath = os.path.dirname(os.path.dirname(me))

        #setup logging
        self._setup_log()

        #PID file name
        rel = os.path.join(self.buildoutpath, 'var', 'worker_%s.pid' % self.id)
        self.pidfile = os.path.abspath(os.path.normpath(rel))
        
        #Check if PID exists
        if os.path.exists(self.pidfile):
            #Is this correct?
            msg = "PID-file already exists. Maybe the script is already running?"
            self.logger.exception(msg)
            sys.exit(msg)
            
        
        #Start wsgi stuff
        config = os.path.join(self.buildoutpath, 'etc', 'development.ini') #FIXME: buildout info for script?
        config = os.path.abspath(os.path.normpath(config))
        self.app = loadapp('config:%s' % config, name='VoteIT')
        self.root, self.closer = get_root(self.app)
        
        print 'Worker initialized'

        #write pid
        self._write_pid_file()

    def _setup_log(self):
        #FIXME: Make this customizable. There might be simpler ways to get this from the wsgi config too.
        #Adapted from http://docs.python.org/howto/logging-cookbook.html
        logger = logging.getLogger('voteit.core.scripts')
        logger.setLevel(logging.INFO)
        
        # create file handler
        rel = os.path.join(self.buildoutpath, 'var', 'log', 'worker_%s.log' % self.id)
        path = os.path.abspath(os.path.normpath(rel))
        fh = logging.FileHandler(path)
        fh.setLevel(logging.INFO)
        
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s][%(threadName)s] %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        self.logger = logger
        
    def _write_pid_file(self):
        with open(self.pidfile, 'w') as f:
            f.write( "%s" % os.getpid() )
    
    def _remove_pid_file(self):
        os.remove(self.pidfile)

    def shutdown(self):
        """ Close the application. """
        self._remove_pid_file()
        sys.exit(0)
