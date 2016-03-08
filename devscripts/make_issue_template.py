#!/usr/bin/env python
from __future__ import unicode_literals

import io
import optparse
import re


def main():
    parser = optparse.OptionParser(usage='%prog FILE')
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Expected an filename')

    with io.open(args[0], encoding='utf-8') as inf:
        issue_template_text = inf.read()

    # Get the version from youtube_dl/version.py without importing the package
    exec(compile(open('youtube_dl/version.py').read(),
         'youtube_dl/version.py', 'exec'))

    issue_template_text = re.sub(
        r'(?<=available \()(?P<version>[0-9\.]+)(?=\))',
        __version__,
        issue_template_text
    )

    with io.open(args[0], 'w', encoding='utf-8') as outf:
         outf.write(issue_template_text)

if __name__ == '__main__':
    main()
