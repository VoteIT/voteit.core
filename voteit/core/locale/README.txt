Handle translations this way.

  1. Go to voteit.core (or any repo that needs translating)
  2. Run: ../../bin/py setup.py extract_messages
  3. Run: ../../bin/py setup.py update_catalog
  4. Make your translations in .po-file
  5. Run: ../../bin/py setup.py compile_catalog
  6. Test
  7. Submit your translation

Read more about it here:

http://docs.pylonsproject.org/projects/pyramid/en/1.2-branch/narr/i18n.html

http://docs.pylonsproject.org/projects/pyramid/en/1.2-branch/narr/i18n.html#updating-a-catalog-file
