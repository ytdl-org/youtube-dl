import os
import glob
import imp
from .compat import (
    compat_expanduser,
    compat_getenv,
)


mdirs = [ os.path.dirname(__file__)+'/auto' ]

def confdirs():
    cfg_home = compat_getenv('XDG_CONFIG_HOME') or compat_getenv('appdata') or os.path.join(compat_expanduser('~'), '.config')

    if cfg_home:
       cfg_dir = os.path.join(cfg_home, 'youtube-dl','modules')
       if os.path.isdir(cfg_dir):
           return [cfg_dir]
    return []

def load_dynamic_extractors(module_dir=None):
    mdirs.extend(confdirs())
    if module_dir != None:
        if not os.path.isdir(module_dir):
            raise OSError('No such directory: '+module_dir)
        mdirs.append(module_dir)

    ret = {}
    for mdir in mdirs:
        files = glob.glob(mdir+"/*.py")
        for f in [ os.path.basename(f)[:-3] for f in files]:
           # force extractor namespace upon /any/path.py
           fh, filename, desc = imp.find_module(f, [mdir])
           module = imp.load_module('youtube_dl.extractor.'+f, fh, filename, desc)

           for name in dir(module):
              if name.endswith('IE') and name != 'GenericIE':
                  ci = getattr(module,name)
                  #globals()[name] = ci
                  ret[name] = ci
                  print('[autoload]: '+mdir+' '+f+': '+name)
    return ret
