import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = (
    'pyramid>=1.2',
    'pyramid_mailer',
    'pyramid_zcml',
    'pyramid_zodbconn',
    'pyramid_tm',
    'repoze.folder',
    'repoze.workflow',
    'ZODB3',
    'WebError',
    'colander',
    'deform>=0.9.5',
    'Babel',
    'slugify',
    'webhelpers',
    'repoze.catalog',
    'lingua',
    'httplib2',
    'betahaus.pyracont>=0.1a3',
    'betahaus.viewcomponent',
    'pyramid_debugtoolbar', #Won't be active unless included
    'fanstatic',
    'repoze.evolution',
    'httpagentparser',
    'BeautifulSoup',
    )


setup(name='voteit.core',
      version='0.0',
      description='Core VoteIT package',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='VoteIT development team',
      author_email='info@voteit.se',
      url='http://www.voteit.se',
      keywords='web pylons pyramid voteit',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = requires,
      tests_require= requires,
      test_suite="voteit.core",
      entry_points = """\
      [paste.app_factory]
      main = voteit.core:main
      [console_scripts]
      update_catalog = voteit.core.scripts.catalog:update_catalog
      evolve = voteit.core.scripts.evolve:main
      debug_instance = voteit.core.scripts.debug:debug_instance
      [fanstatic.libraries]
      voteit_core_csslib = voteit.core.fanstaticlib:voteit_core_csslib
      voteit_core_jslib = voteit.core.fanstaticlib:voteit_core_jslib
      deformlib = voteit.core.fanstaticlib:deformlib
      [paste.paster_create_template]
      voteit_poll_plugin=voteit.core.scaffolds:PollPluginTemplate
      """,
      paster_plugins=['pyramid'],
      message_extractors = { '.': [
              ('**.py',   'lingua_python', None ),
              ('**.pt',   'lingua_xml', None ),
              #The ZCML extractor seems broken in lingua, but since it's ZCML is XML this works. /robinharms
              ('**.zcml',   'lingua_xml', None ),
              ]},
      )
