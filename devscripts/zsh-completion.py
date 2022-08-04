#!/usr/bin/env python
"""Generate zsh completion script.

Usage
-----
.. code-block:: zsh
    devscripts/zsh-completion.py
    sudo mv youtube-dl.zsh /usr/share/zsh/site-functions/_youtube-dl
    rm -f ~/.zcompdump  # optional
    compinit  # regenerate ~/.zcompdump

Debug
-----
.. code-block:: zsh
    devscripts/zsh-completion.py MODULE_NAME -  # will output to stdout

Refer
-----
- https://github.com/ytdl-org/youtube-dl/blob/master/devscripts/zsh-completion.py
- https://github.com/zsh-users/zsh/blob/master/Etc/completion-style-guide

Examples
--------
.. code-block::
    '(- *)'{-h,--help}'[show this help message and exit]'
    |<-1->||<---2--->||<---------------3--------------->|

.. code-block:: console
    % foo --<TAB>
    option
    --help      show this help message and exit
    % foo --help <TAB>
    no more arguments

.. code-block::
    --color'[When to show color. Default: auto. Support: auto, always, never]:when:(auto always never)'
    |<-2->||<------------------------------3------------------------------->||<4>||<--------5-------->|

.. code-block:: console
    % foo --color <TAB>
    when
    always
    auto
    never

.. code-block::
    --color'[When to show color. Default: auto. Support: auto, always, never]:when:((auto\:"only when output is stdout" always\:always never\:never))'
    |<-2->||<------------------------------3------------------------------->||<4>||<--------------------------------5------------------------------->|

.. code-block:: console
    % foo --color <TAB>
    when
    always   always
    auto     only when output is stdout
    never    never

.. code-block::
    --config='[Config file. Default: ~/.config/foo/foo.toml]:config file:_files -g *.toml'
    |<--2-->||<---------------------3--------------------->||<---4---->||<------5------->|

.. code-block:: console
    % foo --config <TAB>
    config file
    a.toml  b/ ...
    ...

.. code-block::
    {1,2}'::_command_names -e'
    |<2->|4|<-------5------->|

.. code-block:: console
    % foo help<TAB>
    _command_names -e
    help2man  generate a simple manual page
    helpviewer
    ...
    % foo hello hello <TAB>
    no more arguments

.. code-block::
    '*: :_command_names -e'
    2|4||<-------5------->|

.. code-block:: console
    % foo help<TAB>
    external command
    help2man  generate a simple manual page
    helpviewer
    ...
    % foo hello hello help<TAB>
    external command
    help2man  generate a simple manual page
    helpviewer
    ...

+----+------------+----------+------+
| id | variable   | required | expr |
+====+============+==========+======+
| 1  | prefix     | F        | (.*) |
| 2  | optionstr  | T        | .*   |
| 3  | helpstr    | F        | [.*] |
| 4  | metavar    | F        | :.*  |
| 5  | completion | F        | :.*  |
+----+------------+----------+------+
"""
from __future__ import unicode_literals
from optparse import SUPPRESS_HELP
import os
from os.path import dirname as dirn
import sys
from typing import Final

from setuptools import find_packages

rootpath = dirn(dirn(os.path.abspath(__file__)))
path = os.path.join(rootpath, "src")
packages = find_packages(path)
if packages == []:
    path = rootpath
sys.path.insert(0, path)
PACKAGE: Final = "youtube_dl" if sys.argv[1:2] == [] else sys.argv[1]
parser = __import__(PACKAGE).parseOpts()[0]
BINNAME: Final = PACKAGE.replace("_", "-")
BINNAMES: Final = [BINNAME]
ZSH_COMPLETION_FILE: Final = (
    "youtube-dl.zsh" if sys.argv[2:3] == [] else sys.argv[2]
)
ZSH_COMPLETION_TEMPLATE = "devscripts/zsh-completion.in"

opts = parser._get_all_options()

flags = []
for opt in opts:
    optionstrs = opt._long_opts + opt._short_opts
    if len(optionstrs) == 1:
        optionstr = optionstrs[0]
    else:
        optionstr = "'{" + ",".join(optionstrs) + "}'"

    if opt.action in ["help", "version"]:
        prefix = "- *"
    else:
        prefix = " ".join(optionstrs)
    prefix = "'(" + prefix + ")"

    if opt.help == SUPPRESS_HELP:
        helpstr = ""
    else:
        helpstr = opt.help.replace("'", "'\\''").replace("]", "\\]")
        helpstr = "[" + helpstr + "]"

    if isinstance(opt.metavar, str):
        metavar = opt.metavar
    elif optionstr == "--external-downloader-args":
        metavar = " "  # use default
    else:  # opt.metavar is None
        metavar = ""
    if metavar != "":
        # use lowcase conventionally
        metavar = metavar.lower().replace(":", "\\:")

    if opt.choices:
        completion = "(" + " ".join(opt.choices) + ")"
    elif optionstr == "--external-downloader-args":
        completion = "->external-downloader-args"
    elif metavar == "file":
        completion = "_files"
        metavar = " "
    elif metavar == "dir":
        completion = "_dirs"
        metavar = " "
    elif metavar == "url":
        completion = "_urls"
        metavar = " "
    elif metavar == "command":
        completion = "_command_names -e"
        metavar = " "
    else:
        completion = ""

    if metavar != "":
        metavar = ":" + metavar
    if completion != "":
        completion = ":" + completion

    flag = "{0}{1}{2}{3}{4}'".format(
        prefix, optionstr, helpstr, metavar, completion
    )

    flags += [flag]

with open(ZSH_COMPLETION_TEMPLATE) as f:
    template = f.read()

template = template.replace("{{programs}}", " ".join(BINNAMES))
template = template.replace("{{flags}}", " \\\n  ".join(flags))

with (
    open(ZSH_COMPLETION_FILE, "w")
    if ZSH_COMPLETION_FILE != "-"
    else sys.stdout
) as f:
    f.write(template)
