 #!/bin/bash
 #You need lingua and gettext installed to run this
 
 echo "Updating voteit.core.pot"
 pot-create -d voteit.core -o voteit/core/locale/voteit.core.pot .
 echo "Merging Swedish localisation"
 msgmerge --update voteit/core/locale/sv/LC_MESSAGES/voteit.core.po voteit/core/locale/voteit.core.pot
 echo "Updated locale files"
 