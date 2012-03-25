from distutils.core import setup
import py2exe
import sys

# If run without args, build executables
if len(sys.argv) == 1:
    sys.argv.append("py2exe")

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

setup(
    console = console,
    options = {"py2exe": options},
    zipfile = None,
)

import shutil
shutil.rmtree("build")

