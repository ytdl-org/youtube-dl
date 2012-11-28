#!/usr/bin/env python
from setuptools import setup
from setuptools import find_packages

version = '1.3.6'

setup(name='youtube-dl',
      version=version,
      description="YouTube downloader",
      long_description="""\
**youtube-dl** is a small command-line program to download videos from
YouTube.com and a few more sites. It requires the Python interpreter, version
2.x (x being at least 6), and it is not platform specific. It should work in
your Unix box, in Windows or in Mac OS X. It is released to the public domain,
which means you can modify it, redistribute it or use it however you like.
""",
      packages=find_packages(exclude=['test']),
      include_package_data=True,
      zip_safe=False,
      entry_points="""
      [console_scripts]
      youtube-dl = youtube_dl:main
      """,
      )
