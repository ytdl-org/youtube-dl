#!/usr/bin/env python3

import datetime
import io
import json
import textwrap


atom_template = textwrap.dedent("""\
    <?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>youtube-dl releases</title>
        <id>https://yt-dl.org/feed/youtube-dl-updates-feed</id>
        <updated>@TIMESTAMP@</updated>
        @ENTRIES@
    </feed>""")

entry_template = textwrap.dedent("""
    <entry>
        <id>https://yt-dl.org/feed/youtube-dl-updates-feed/youtube-dl-@VERSION@</id>
        <title>New version @VERSION@</title>
        <link href="http://rg3.github.io/youtube-dl" />
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
    entry = entry_template.replace('@TIMESTAMP@', v.replace('.', '-') + 'T00:00:00Z')
    entry = entry.replace('@VERSION@', v)
    entries.append(entry)

entries_str = textwrap.indent(''.join(entries), '\t')
atom_template = atom_template.replace('@ENTRIES@', entries_str)

with io.open('update/releases.atom', 'w', encoding='utf-8') as atom_file:
    atom_file.write(atom_template)

