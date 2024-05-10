#!/usr/bin/env python
from __future__ import unicode_literals

import optparse
import re

from utils import read_file, write_file


def main():
    parser = optparse.OptionParser(usage='%prog INFILE OUTFILE')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Expected an input and an output filename')

    infile, outfile = args

    readme = read_file(infile)

    bug_text = re.search(
        r'(?s)#\s*BUGS\s*[^\n]*\s*(.*?)#\s*COPYRIGHT', readme).group(1)
    dev_text = re.search(
        r'(?s)(#\s*DEVELOPER INSTRUCTIONS.*?)#\s*EMBEDDING YOUTUBE-DL',
        readme).group(1)

    out = bug_text + dev_text

    write_file(outfile, out)


if __name__ == '__main__':
    main()
