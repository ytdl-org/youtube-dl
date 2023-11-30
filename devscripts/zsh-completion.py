#!/usr/bin/env python
from __future__ import unicode_literals

import os
from os.path import dirname as dirn
import sys
import optparse

sys.path.insert(0, dirn(dirn((os.path.abspath(__file__)))))
import youtube_dl
from utils import read_file, write_file


ZSH_COMPLETION_FILE = "youtube-dl.zsh"
ZSH_COMPLETION_TEMPLATE = "devscripts/zsh-completion.in"


def build_completion(opt_parser):
    opts = [opt for group in opt_parser.option_groups
            for opt in group.option_list]

    # escaping is hard:
    #  - help may contain colons
    #  - metavar must have colons : escaped
    #  - single quotes must be removed
    #  - help must have square brackets [] escaped
    def metaparse(opt):
        if "--recode-video" == opt.get_opt_string():
            return ":{}:(mp4 flv ogg webm mkv)".format(opt.metavar)
        if opt.metavar is None:
            return ""
        if opt.metavar == "FILE":
            return ":FILE:_files"
        if opt.metavar == "DIR":
            return ":DIR:_directories"
        else:
            return ":{}:".format(opt.metavar.replace(":", "\\:"))

    def helpescape(opthelp):
        if opthelp == optparse.SUPPRESS_HELP:
            return ""
        return "[{}]".format(opthelp.replace("'", "\"").replace("]", "\\]").replace("[", "\\["))

    def optionexclude(opt):
        # When an argument has a long and short version, the arguments entry shall be
        # _arguments \
        #   "(-t --thing)"{-t,--thing}"[do things]:WHAT_THING:"
        # i.e. in parentheses with space the explanation of redundancy and in curly braces
        # regular shell expansion to create two mostly identical entries.
        if opt._short_opts:
            return "({0} {1})'{{{0},{1}}}'".format(opt._short_opts[0], opt.get_opt_string())
        return "{}".format(opt.get_opt_string())

    mytest = ["'{}{}{}'".format(optionexclude(opt), helpescape(opt.help), metaparse(opt)) for opt in opts]

    template = read_file(ZSH_COMPLETION_TEMPLATE)

    template = template.replace("{{args}}", " \\\n      ".join(mytest))

    write_file(ZSH_COMPLETION_FILE, template)


parser = youtube_dl.parseOpts()[0]
build_completion(parser)
