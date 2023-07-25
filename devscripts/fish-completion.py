#!/usr/bin/env python
from __future__ import unicode_literals

import optparse
import os
from os.path import dirname as dirn
import sys

sys.path.insert(0, dirn(dirn(os.path.abspath(__file__))))

import youtube_dl
from youtube_dl.utils import shell_quote

from utils import read_file, write_file

FISH_COMPLETION_FILE = 'youtube-dl.fish'
FISH_COMPLETION_TEMPLATE = 'devscripts/fish-completion.in'

EXTRA_ARGS = {
    'recode-video': ['--arguments', 'mp4 flv ogg webm mkv', '--exclusive'],

    # Options that need a file parameter
    'download-archive': ['--require-parameter'],
    'cookies': ['--require-parameter'],
    'load-info': ['--require-parameter'],
    'batch-file': ['--require-parameter'],
}


def build_completion(opt_parser):
    commands = []

    for group in opt_parser.option_groups:
        for option in group.option_list:
            long_option = option.get_opt_string().strip('-')
            complete_cmd = ['complete', '--command', 'youtube-dl', '--long-option', long_option]
            if option._short_opts:
                complete_cmd += ['--short-option', option._short_opts[0].strip('-')]
            if option.help != optparse.SUPPRESS_HELP:
                complete_cmd += ['--description', option.help]
            complete_cmd.extend(EXTRA_ARGS.get(long_option, []))
            commands.append(shell_quote(complete_cmd))

    template = read_file(FISH_COMPLETION_TEMPLATE)
    filled_template = template.replace('{{commands}}', '\n'.join(commands))
    write_file(FISH_COMPLETION_FILE, filled_template)


parser = youtube_dl.parseOpts()[0]
build_completion(parser)
