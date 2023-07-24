#!/usr/bin/env python
from __future__ import unicode_literals

import optparse
import os.path
import sys

# Import youtube_dl
dirn = os.path.dirname

sys.path.insert(0, dirn(dirn(os.path.abspath(__file__))))

import youtube_dl

from utils import write_file


def main():
    parser = optparse.OptionParser(usage='%prog OUTFILE.md')
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Expected an output filename')

    outfile, = args

    def gen_ies_md(ies):
        for ie in ies:
            ie_md = '**{0}**'.format(ie.IE_NAME)
            ie_desc = getattr(ie, 'IE_DESC', None)
            if ie_desc is False:
                continue
            if ie_desc is not None:
                ie_md += ': {0}'.format(ie.IE_DESC)
            if not ie.working():
                ie_md += ' (Currently broken)'
            yield ie_md

    ies = sorted(youtube_dl.gen_extractors(), key=lambda i: i.IE_NAME.lower())
    out = '# Supported sites\n' + ''.join(
        ' - ' + md + '\n'
        for md in gen_ies_md(ies))

    write_file(outfile, out)


if __name__ == '__main__':
    main()
