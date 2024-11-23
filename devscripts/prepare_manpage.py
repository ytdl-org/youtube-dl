from __future__ import unicode_literals

import optparse
import os.path
import re

from utils import read_file, write_file

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_FILE = os.path.join(ROOT_DIR, 'README.md')
PREFIX = r'''%YOUTUBE-DL(1)

# NAME

youtube\-dl \- download videos from youtube.com or other video platforms

# SYNOPSIS

**youtube-dl** \[OPTIONS\] URL [URL...]

'''


def main():
    parser = optparse.OptionParser(usage='%prog OUTFILE.md')
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Expected an output filename')

    outfile, = args

    readme = read_file(README_FILE)

    readme = re.sub(r'(?s)^.*?(?=# DESCRIPTION)', '', readme)
    readme = re.sub(r'\s+youtube-dl \[OPTIONS\] URL \[URL\.\.\.\]', '', readme)
    readme = PREFIX + readme

    readme = filter_options(readme)

    write_file(outfile, readme)


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
                split = re.split(r'\s{2,}', line.lstrip())
                # Description string may start with `-` as well. If there is
                # only one piece then it's a description bit not an option.
                if len(split) > 1:
                    option, description = split
                    split_option = option.split(' ')

                    if not split_option[-1].startswith('-'):  # metavar
                        option = ' '.join(split_option[:-1] + ['*%s*' % split_option[-1]])

                    # Pandoc's definition_lists. See http://pandoc.org/README.html
                    # for more information.
                    ret += '\n%s\n:   %s\n' % (option, description)
                    continue
            ret += line.lstrip() + '\n'
        else:
            ret += line + '\n'

    return ret


if __name__ == '__main__':
    main()
