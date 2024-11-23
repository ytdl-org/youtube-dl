#!/usr/bin/env python3
from __future__ import unicode_literals

import datetime
import json
import os.path
import textwrap
import sys

dirn = os.path.dirname

sys.path.insert(0, dirn(dirn(os.path.abspath(__file__))))

from utils import write_file

atom_template = textwrap.dedent("""\
    <?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <link rel="self" href="http://ytdl-org.github.io/youtube-dl/update/releases.atom" />
        <title>youtube-dl releases</title>
        <id>https://yt-dl.org/feed/youtube-dl-updates-feed</id>
        <updated>@TIMESTAMP@</updated>
        @ENTRIES@
    </feed>""")

entry_template = textwrap.dedent("""
    <entry>
        <id>https://yt-dl.org/feed/youtube-dl-updates-feed/youtube-dl-@VERSION@</id>
        <title>New version @VERSION@</title>
        <link href="http://ytdl-org.github.io/youtube-dl" />
        <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
                Downloads available at <a href="https://yt-dl.org/downloads/@VERSION@/">https://yt-dl.org/downloads/@VERSION@/</a>
            </div>
        </content>
        <author>
            <name>The youtube-dl maintainers</name>
        </author>
        <updated>@TIMESTAMP@</updated>
    </entry>
    """)

now = datetime.datetime.now()
now_iso = now.isoformat() + 'Z'

atom_template = atom_template.replace('@TIMESTAMP@', now_iso)

versions_info = json.load(open('update/versions.json'))
versions = list(versions_info['versions'].keys())
versions.sort()

entries = []
for v in versions:
    fields = v.split('.')
    year, month, day = map(int, fields[:3])
    faked = 0
    patchlevel = 0
    while True:
        try:
            datetime.date(year, month, day)
        except ValueError:
            day -= 1
            faked += 1
            assert day > 0
            continue
        break
    if len(fields) >= 4:
        try:
            patchlevel = int(fields[3])
        except ValueError:
            patchlevel = 1
    timestamp = '%04d-%02d-%02dT00:%02d:%02dZ' % (year, month, day, faked, patchlevel)

    entry = entry_template.replace('@TIMESTAMP@', timestamp)
    entry = entry.replace('@VERSION@', v)
    entries.append(entry)

entries_str = textwrap.indent(''.join(entries), '\t')
atom_template = atom_template.replace('@ENTRIES@', entries_str)

write_file('update/releases.atom', atom_template)
