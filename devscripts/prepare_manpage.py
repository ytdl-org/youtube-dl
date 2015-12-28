from __future__ import unicode_literals

import io
import os.path
import sys
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_FILE = os.path.join(ROOT_DIR, 'README.md')


def filter_options(readme):
    ret = ''
    in_options = False
    for line in readme.split('\n'):
        if line.startswith('# '):
            if line[2:].startswith('OPTIONS'):
                in_options = True
            else:
                in_options = False

        if in_options:
            if line.lstrip().startswith('-'):
                option, description = re.split(r'\s{2,}', line.lstrip())
                split_option = option.split(' ')

                if not split_option[-1].startswith('-'):  # metavar
                    option = ' '.join(split_option[:-1] + ['*%s*' % split_option[-1]])

                # Pandoc's definition_lists. See http://pandoc.org/README.html
                # for more information.
                ret += '\n%s\n:   %s\n' % (option, description)
            else:
                ret += line.lstrip() + '\n'
        else:
            ret += line + '\n'

    return ret

with io.open(README_FILE, encoding='utf-8') as f:
    readme = f.read()

PREFIX = '''%YOUTUBE-DL(1)

# NAME

youtube\-dl \- download videos from youtube.com or other video platforms

# SYNOPSIS

**youtube-dl** \[OPTIONS\] URL [URL...]

'''
readme = re.sub(r'(?s)^.*?(?=# DESCRIPTION)', '', readme)
readme = re.sub(r'\s+youtube-dl \[OPTIONS\] URL \[URL\.\.\.\]', '', readme)
readme = PREFIX + readme

readme = filter_options(readme)

if sys.version_info < (3, 0):
    print(readme.encode('utf-8'))
else:
    print(readme)
