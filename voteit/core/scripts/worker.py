import os
import sys

from paste.deploy import loadapp
from pyramid.scripting import get_root


class ScriptWorker(object):
    
    pidfile = None
    buildoutpath = None
    id = None
    root = None
    closer = None
    
    def __init__(self, id):
        """ Initialize worker.
            id will be part of the pid-file.
        """
        #Get paster app configuration file
        self.id = id
        me = sys.argv[0]
        me = os.path.abspath(me)
        
        #Usefull later
        self.buildoutpath = os.path.dirname(os.path.dirname(me))

        #PID file name
        rel = os.path.join(self.buildoutpath, 'var', 'worker_%s.pid' % self.id)
        self.pidfile = os.path.abspath(os.path.normpath(rel))
        
        #Check if PID exists
        if os.path.exists(self.pidfile):
            sys.exit("PID-file already exists. Maybe the script is already running?")
        
        #Start wsgi stuff
        config = os.path.join(self.buildoutpath, 'etc', 'development.ini') #FIXME: buildout info for script?
        config = os.path.abspath(os.path.normpath(config))
        app = loadapp('config:%s' % config, name='voteit.core')
        self.root, self.closer = get_root(app)

        print 'Worker initialized'

        #write pid
        self._write_pid_file()

    def _write_pid_file(self):
        with open(self.pidfile, 'w') as f:
            f.write( "%s" % os.getpid() )
    
    def _remove_pid_file(self):
        os.remove(self.pidfile)

    def shutdown(self):
        """ Close the application. """
        print 'Comitting changes'
        self._remove_pid_file()
        sys.exit(0)
