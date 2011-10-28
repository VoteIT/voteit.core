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
    'colander>=0.9.4',
    'deform>=0.9.1',
    'Babel',
    'slugify',
    'webtest',
    'zope.testbrowser',
    'webhelpers',
    'repoze.catalog',
    'lingua',
    'httplib2',
    'betahaus.pyracont',
    'betahaus.viewcomponent',
    'pyramid_debugtoolbar', #Won't be active unless included
    'fanstatic',
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
      author='',
      author_email='',
      url='',
      keywords='web pylons pyramid',
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
      [fanstatic.libraries]
      voteit_core_css = voteit.core.fanstaticlib:voteit_core_css
      voteit_core_js = voteit.core.fanstaticlib:voteit_core_js
      deform_static = voteit.core.fanstaticlib:deform_static
      """,
      paster_plugins=['pyramid'],
      message_extractors = { '.': [
              ('**.py',   'lingua_python', None ),
              ('**.pt',   'lingua_xml', None ),
              ('**.zcml',   'lingua_zcml', None ),
              ]},
      )
