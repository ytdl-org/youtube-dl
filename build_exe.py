from distutils.core import setup
import py2exe
import sys, os

"""This will create an exe that needs Microsoft Visual C++ 2008 Redistributable Package"""

# If run without args, build executables
if len(sys.argv) == 1:
    sys.argv.append("py2exe")

# os.chdir(os.path.dirname(os.path.abspath(sys.argv[0]))) # conflict with wine-py2exe.sh
sys.path.append('./youtube_dl')

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
for line in init_file.readlines():
    if line.startswith('__version__'):
        version = line[11:].strip(" ='\n")
        break
else:
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

