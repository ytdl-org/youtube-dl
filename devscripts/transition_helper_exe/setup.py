from distutils.core import setup
import py2exe

py2exe_options = {
    "bundle_files": 1,
    "compressed": 1,
    "optimize": 2,
    "dist_dir": '.',
    "dll_excludes": ['w9xpopen.exe']
}

setup(console=['youtube-dl.py'], options={ "py2exe": py2exe_options }, zipfile=None)