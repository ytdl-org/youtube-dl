#!/usr/bin/env python
from __future__ import unicode_literals

import argparse
import io
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'INFILE', help='README.md file name to read from')
    parser.add_argument(
        'OUTFILE', help='CONTRIBUTING.md file name to write to')
    args = parser.parse_args()

    with io.open(args.INFILE, encoding='utf-8') as inf:
        readme = inf.read()

    bug_text = re.search(
        r'(?s)#\s*BUGS\s*[^\n]*\s*(.*?)#\s*COPYRIGHT', readme).group(1)
    dev_text = re.search(
        r'(?s)(#\s*DEVELOPER INSTRUCTIONS.*?)#\s*EMBEDDING YOUTUBE-DL',
        readme).group(1)

    out = bug_text + dev_text

    with io.open(args.OUTFILE, 'w', encoding='utf-8') as outf:
        outf.write(out)

if __name__ == '__main__':
    main()
