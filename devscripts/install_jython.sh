#!/bin/bash
 
version="jython-installer-2.7.2.jar"
url="https://repo1.maven.org/maven2/org/python/jython-installer/2.7.2/jython-installer-2.7.2.jar"
pkg="java"
pkg_ok=$(dpkg-query -W --showformat='${Status}\n' $pkg | grep "install ok installed")
 
echo "Downloading source"
#wget $url
echo "Installing jython"
if [ "" = "$pkg_ok" ]; then 
	echo "$pkg is not installed. Setting this up now."
	apt-get update
	apt-get install openjdk-8-jdk
	java - version
fi
java -jar $version -s -d "$HOME/jython"
echo "Installing nose"
$HOME/jython/bin/jython -m pip install nose