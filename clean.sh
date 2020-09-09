#!/bin/bash

# Not sure what the ideal order of these are

find streamfield/ -iname "*.py" -print | grep -v '/migrations/' | grep -v 'manage.py' | xargs -P8 -n1 autopep8 --max-line-length 119 --in-place
find streamfield/ -iname "*.py" -print | grep -v '/migrations/' | grep -v 'manage.py' | xargs -P8 -n1 autoflake -i --remove-all-unused-imports
find streamfield/ -iname "*.py" -print | grep -v '/migrations/' | grep -v 'manage.py' | xargs -P8 -n1 isort -y -w 119
