from distutils.core import setup
import sys
try:
    import py2exe
except ImportError:
    sys.stderr.write("Cannot import py2exe")
import os
import subprocess

"""The p2exe option will create an exe that needs Microsoft Visual C++ 2008 Redistributable Package.
    python setup.py py2exe
   You can also build a zip executable with
    python setup.py bdist --format=zip


"""

# If run without args, build executables
if len(sys.argv) == 1:
    sys.argv.append("py2exe")

# os.chdir(os.path.dirname(os.path.abspath(sys.argv[0]))) # conflict with wine-py2exe.sh
#sys.path.append('./youtube_dl')

options = {
    "bundle_files": 1,
    "compressed": 1,
    "optimize": 2,
    "dist_dir": '.',
    "dll_excludes": ['w9xpopen.exe']
}

console = [{
    "script":"./youtube_dl/__main__.py",
    "dest_base": "youtube-dl",
}]

init_file = open('./youtube_dl/__init__.py')

try:
    version = subprocess.checkoutput(["git", "describe", "--abbrev=0", "--tags"])
except:
    version = ''

setup(name='youtube-dl',
      version=version,
      description='Small command-line program to download videos from YouTube.com and other video sites',
      url='https://github.com/rg3/youtube-dl',
      packages=['youtube_dl'],

      console = console,
      options = {"py2exe": options},
      zipfile = None,
)

import shutil
shutil.rmtree("build")

