#!/usr/bin/env python
from __future__ import unicode_literals

import optparse
import os.path
import sys

from utils import read_file, read_version, write_file


def main():
    parser = optparse.OptionParser(usage='%prog INFILE OUTFILE')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Expected an input and an output filename')

    infile, outfile = args

    issue_template_tmpl = read_file(infile)

    out = issue_template_tmpl % {'version': read_version()}

    write_file(outfile, out)

if __name__ == '__main__':
    main()
