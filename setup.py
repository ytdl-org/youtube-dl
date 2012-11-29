#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from distutils.core import setup
import pkg_resources
import sys

try:
    import py2exe
except ImportError:
    print("Cannot import py2exe", file=sys.stderr)

py2exe_options = {
    "bundle_files": 1,
    "compressed": 1,
    "optimize": 2,
    "dist_dir": '.',
    "dll_excludes": ['w9xpopen.exe']
}

py2exe_console = [{
    "script":"./youtube_dl/__main__.py",
    "dest_base": "youtube-dl",
}]

exec(compile(open('youtube_dl/version.py').read(), 'youtube_dl/version.py', 'exec'))

setup(
    name = 'youtube_dl',
    version = __version__,
    description = 'Small command-line program to download videos from YouTube.com and other video sites',
    url = 'https://github.com/rg3/youtube-dl',
    author = 'Ricardo Garcia',
    maintainer = 'Philipp Hagemeister',
    maintainer_email = 'phihag@phihag.de',
    packages = ['youtube_dl'],

    test_suite = 'nose.collector',
    test_requires = ['nosetest'],

    console = py2exe_console,
    options = { "py2exe": py2exe_options },

    scripts = ['bin/youtube-dl'],
    zipfile = None,

    classifiers = [
        "Topic :: Multimedia :: Video",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: Public Domain",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3"
    ]
)
