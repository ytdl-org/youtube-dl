#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

"""
This script displays the API parameters corresponding to a yt-dl command line

Example:
$ ./cli_to_api.py -f best
{u'format': 'best'}
$
"""

# Allow direct execution
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youtube_dl
from types import MethodType


def cli_to_api(*opts):
    YDL = youtube_dl.YoutubeDL

    # to extract the parsed options, break out of YoutubeDL instantiation

    # return options via this Exception
    class ParseYTDLResult(Exception):
        def __init__(self, result):
            super(ParseYTDLResult, self).__init__('result')
            self.opts = result

    # replacement constructor that raises ParseYTDLResult
    def ytdl_init(ydl, ydl_opts):
        super(YDL, ydl).__init__(ydl_opts)
        raise ParseYTDLResult(ydl_opts)

    # patch in the constructor
    YDL.__init__ = MethodType(ytdl_init, YDL)

    # core parser
    def parsed_options(argv):
        try:
            youtube_dl._real_main(list(argv))
        except ParseYTDLResult as result:
            return result.opts

    # from https://github.com/yt-dlp/yt-dlp/issues/5859#issuecomment-1363938900
    default = parsed_options([])

    def neq_opt(a, b):
        if a == b:
            return False
        if a is None and repr(type(object)).endswith(".utils.DateRange'>"):
            return '0001-01-01 - 9999-12-31' != '{0}'.format(b)
        return a != b

    diff = dict((k, v) for k, v in parsed_options(opts).items() if neq_opt(default[k], v))
    if 'postprocessors' in diff:
        diff['postprocessors'] = [pp for pp in diff['postprocessors'] if pp not in default['postprocessors']]
    return diff


def main():
    from pprint import PrettyPrinter

    pprint = PrettyPrinter()
    super_format = pprint.format

    def format(object, context, maxlevels, level):
        if repr(type(object)).endswith(".utils.DateRange'>"):
            return '{0}: {1}>'.format(repr(object)[:-2], object), True, False
        return super_format(object, context, maxlevels, level)

    pprint.format = format

    pprint.pprint(cli_to_api(*sys.argv))


if __name__ == '__main__':
    main()
