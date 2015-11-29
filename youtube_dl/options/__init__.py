import sys

if sys.version_info >= (2,7,0):
    from .options_argparse import parseOpts
else:
    from .options import parseOpts
