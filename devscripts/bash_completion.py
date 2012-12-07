#!/usr/bin/env python2
import youtube_dl

BASH_COMPLETION_FILE = "youtube-dl.bash_completion"
BASH_COMPLETION_TEMPLATE = "devscripts/bash_completion.template"

def build_completion(opt_parser):
    opts_flag = []
    for group in opt_parser.option_groups:
        for option in group.option_list:
            #for every long flag
            opts_flag.append(option.get_opt_string())
    with open(BASH_COMPLETION_TEMPLATE) as f:
        template = f.read()
    with open(BASH_COMPLETION_FILE, "w") as f:
        #just using the special char
        print opts_flag
        filled_template = template.replace("{{flags}}", " ".join(opts_flag))
        f.write(filled_template)

parser = youtube_dl.parseOpts()[0]
build_completion(parser)
