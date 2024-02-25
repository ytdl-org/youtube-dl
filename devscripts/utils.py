# coding: utf-8
from __future__ import unicode_literals

import argparse
import functools
import os.path
import subprocess
import sys

dirn = os.path.dirname

sys.path.insert(0, dirn(dirn(os.path.abspath(__file__))))

from youtube_dl.compat import (
    compat_kwargs,
    compat_open as open,
)


def read_file(fname):
    with open(fname, encoding='utf-8') as f:
        return f.read()


def write_file(fname, content, mode='w'):
    with open(fname, mode, encoding='utf-8') as f:
        return f.write(content)


def read_version(fname='youtube_dl/version.py'):
    """Get the version without importing the package"""
    exec(compile(read_file(fname), fname, 'exec'))
    return locals()['__version__']


def get_filename_args(has_infile=False, default_outfile=None):
    parser = argparse.ArgumentParser()
    if has_infile:
        parser.add_argument('infile', help='Input file')
    kwargs = {'nargs': '?', 'default': default_outfile} if default_outfile else {}
    kwargs['help'] = 'Output file'
    parser.add_argument('outfile', **compat_kwargs(kwargs))

    opts = parser.parse_args()
    if has_infile:
        return opts.infile, opts.outfile
    return opts.outfile


def compose_functions(*functions):
    return lambda x: functools.reduce(lambda y, f: f(y), functions, x)


def run_process(*args, **kwargs):
    kwargs.setdefault('text', True)
    kwargs.setdefault('check', True)
    kwargs.setdefault('capture_output', True)
    if kwargs['text']:
        kwargs.setdefault('encoding', 'utf-8')
        kwargs.setdefault('errors', 'replace')
        kwargs = compat_kwargs(kwargs)
    return subprocess.run(args, **kwargs)
