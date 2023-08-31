#!/usr/bin/env python3
from __future__ import unicode_literals

import sys
import os
import textwrap

dirn = os.path.dirname

# We must be able to import youtube_dl
sys.path.insert(0, dirn(dirn(dirn(os.path.abspath(__file__)))))

import youtube_dl
from devscripts.utils import read_file, write_file


def main():
    template = read_file('supportedsites.html.in')

    ie_htmls = []
    for ie in youtube_dl.list_extractors(age_limit=None):
        ie_html = '<b>{}</b>'.format(ie.IE_NAME)
        ie_desc = getattr(ie, 'IE_DESC', None)
        if ie_desc is False:
            continue
        elif ie_desc is not None:
            ie_html += ': {}'.format(ie.IE_DESC)
        if not ie.working():
            ie_html += ' (Currently broken)'
        ie_htmls.append('<li>{}</li>'.format(ie_html))

    template = template.replace('@SITES@', textwrap.indent('\n'.join(ie_htmls), '\t'))

    write_file('supportedsites.html', template)


if __name__ == '__main__':
    main()
