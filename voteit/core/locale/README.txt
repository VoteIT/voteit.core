Translation trouble!

We've tried to extract messages with Babel, but that doesn't work in a lot of cases,
like macro templates. So we're using a mix of Babel and i18ndude to extract and compile
mo-files now.

Extraction - from dir voteit/core:
i18ndude rebuild-pot --pot locale/voteit.core.pot --create voteit.core .
i18ndude sync --pot locale/voteit.core.pot locale/sv/LC_MESSAGES/voteit.core.po

(You need to install i18ndude before running the command. It's available on pypi.python.org)

Compiling with Babel
From the eggs root dir, Ie src/voteit.core in our current dev enviroment:
../../bin/py setup.py compile_catalog

We'll try to resolve this problem ASAP, until then we'll have to rely on both tools.

/Robin
