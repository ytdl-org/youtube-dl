#!/usr/bin/env python3

import datetime

import textwrap

import json

atom_template=textwrap.dedent("""\
								<?xml version='1.0' encoding='utf-8'?>
								<atom:feed xmlns:atom="http://www.w3.org/2005/Atom">
									<atom:title>youtube-dl releases</atom:title>
									<atom:id>youtube-dl-updates-feed</atom:id>
									<atom:updated>@TIMESTAMP@</atom:updated>
									@ENTRIES@
								</atom:feed>""")

entry_template=textwrap.dedent("""
								<atom:entry>
									<atom:id>youtube-dl-@VERSION@</atom:id>
									<atom:title>New version @VERSION@</atom:title>
									<atom:link href="http://rg3.github.io/youtube-dl" />
									<atom:content type="xhtml">
										<div xmlns="http://www.w3.org/1999/xhtml">
											Downloads available at <a href="https://yt-dl.org/downloads/@VERSION@/">https://yt-dl.org/downloads/@VERSION@/</a>
										</div>
									</atom:content>
									<atom:author>
										<atom:name>The youtube-dl maintainers</atom:name>
									</atom:author>
									<atom:updated>@TIMESTAMP@</atom:updated>
								</atom:entry>
								""")

now = datetime.datetime.now()
now_iso = now.isoformat()

atom_template = atom_template.replace('@TIMESTAMP@',now_iso)

entries=[]

versions_info = json.load(open('update/versions.json'))
versions = list(versions_info['versions'].keys())
versions.sort()

for v in versions:
	entry = entry_template.replace('@TIMESTAMP@',v.replace('.','-'))
	entry = entry.replace('@VERSION@',v)
	entries.append(entry)

entries_str = textwrap.indent(''.join(entries), '\t')
atom_template = atom_template.replace('@ENTRIES@', entries_str)

with open('update/releases.atom','w',encoding='utf-8') as atom_file:
	atom_file.write(atom_template)

