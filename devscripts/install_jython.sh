#!/bin/bash

wget http://central.maven.org/maven2/org/python/jython-installer/2.7.1/jython-installer-2.7.1.jar
java -jar jython-installer-2.7.1.jar -s -d "$HOME/jython"
$HOME/jython/bin/jython -m pip install nose
