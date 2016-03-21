#!/bin/sh

if [ "$TESTS" = "complete" ]; then
	exec nosetests test --verbose
else
	exec ./devscripts/regdetect.py
fi
