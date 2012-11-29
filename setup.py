from distutils.core import setup, Command
import sys
try:
    import py2exe
except ImportError:
    sys.stderr.write("Cannot import py2exe")
import subprocess

"""The p2exe option will create an exe that needs Microsoft Visual C++ 2008 Redistributable Package.
    python setup.py py2exe
   You can also build a zip executable with
    python setup.py bdist --format=zip

   The test suite can be run with
    python setup.py test


    The actual version is defined by the last git tag
"""

# If run without args, build executables
#if len(sys.argv) == 1:
#    sys.argv.append("py2exe")

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
    #return the last tag name
    version = subprocess.checkoutput(["git", "describe", "--abbrev=0", "--tags"])
except:
    version = ''

setup(name='youtube-dl',
      version=version,
      long_description='Small command-line program to download videos from YouTube.com and other video sites',
      url='https://github.com/rg3/youtube-dl',
      packages=['youtube_dl'],
      #test suite
      test_suite='nose.collector',
      test_requires=['nosetest'],
      console=console,
      options={"py2exe": options},
      scripts=['bin/youtube-dl'],
      zipfile=None,
)

#import shutil
#shutil.rmtree("build")

