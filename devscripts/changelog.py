#!/usr/bin/env python
from __future__ import unicode_literals

import os
import subprocess
import sys


def run(args):
    process = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)
    return process.communicate()[0].strip()


def is_core(short):
    prefix = None
    if ']' in short:
        prefix = short.partition(']')[0][1:]
    elif ': ' in short:
        prefix = short.partition(': ')[0]

    if not prefix or ' ' in prefix:
        return True

    prefix = prefix.partition(':')[0].lower()
    if prefix.startswith('extractor/'):
        prefix = prefix[len('extractor/'):]
    if prefix.endswith('ie'):
        prefix = prefix[:-len('ie')]
    return not os.path.exists('youtube_dl/extractor/%s.py' % prefix)


def format_line(markdown, short, sha):
    if not markdown:
        return '* ' + short

    return '* [%s](https://github.com/ytdl-org/youtube-dl/commit/%s)' % (short, sha)


def generate_changelog(markdown):
    most_recent_tag = run([
        'git', 'tag', '--list', '--sort=-v:refname',
        '????.??.??', '????.??.??.?',
    ]).split('\n')[0]
    lines = run([
        'git', 'log',
        '--format=format:%H%n%s', '--no-merges', '-z',
        most_recent_tag + '..HEAD',
    ]).split('\x00')

    core = []
    extractor = []
    for line in lines:
        if not line:
            continue
        sha, short = line.split('\n')

        if ' * ' in short:
            short = short.partition(' * ')[0]

        target = core if is_core(short) else extractor
        target.append((sha, short))

    result = []
    if core:
        result.append('#### Core' if markdown else 'Core')
        for sha, short in core:
            result.append(format_line(markdown, short, sha))
        result.append('')

    if extractor:
        result.append('#### Extractor' if markdown else 'Extractor')
        for sha, short in extractor:
            result.append(format_line(markdown, short, sha))
        result.append('')

    return '\n'.join(result)


def read_version():
    with open('youtube_dl/version.py', 'r') as f:
        exec(compile(f.read(), 'youtube_dl/version.py', 'exec'))

    return locals()['__version__']


update_in_place = len(sys.argv) > 1 and sys.argv[1] == '--update'
changelog = generate_changelog(not update_in_place)

if not update_in_place:
    print(changelog)
    sys.exit()

with open('ChangeLog', 'rb') as file:
    data = file.read()

with open('ChangeLog', 'wb') as file:
    file.write(('version %s\n\n' % read_version()).encode('utf-8'))
    file.write(changelog.encode('utf-8'))
    file.write('\n\n'.encode('utf-8'))
    file.write(data)
