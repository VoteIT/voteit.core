import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

install_requires = (
    'Arche',
    'beautifulsoup4', #FIXME?
    'ZODB3',
    'arche_usertags',
    'betahaus.pyracont >= 0.3b', #Needed for migrations
    'betahaus.viewcomponent',
    'colander',
    'deform',
    'fanstatic',
    'html2text',
    'js.jquery_tablesorter', #FIXME?
    'pyramid',
    'pyramid_zcml',
    'repoze.workflow',
    'webhelpers',
    'redis<3.5',
    'pyramid-auto-env',
    'pyramid_retry',
    'pyramid_exclog',
)

docs_extras = [
    'Sphinx',
    'docutils',
    'repoze.sphinx.autointerface',
    ]

testing_extras = [
    'nose',
    'coverage',
    'fakeredis<1.2',
    ]

setup(name='voteit.core',
      version='0.2dev',
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
      install_requires = install_requires,
      extras_require = {
          'testing': testing_extras,
          'docs': docs_extras,
          },
      tests_require = install_requires,
      test_suite="voteit.core",
      entry_points = """\
      [paste.app_factory]
      main = voteit.core:main
      [fanstatic.libraries]
      voteit_core_csslib = voteit.core.fanstaticlib:voteit_core_csslib
      voteit_core_jslib = voteit.core.fanstaticlib:voteit_core_jslib
      deformlib = voteit.core.fanstaticlib:deformlib
      """,)
