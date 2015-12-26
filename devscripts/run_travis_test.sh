#!/bin/bash

python devscripts/i18n.py update-gmo
nosetests test --verbose
