#!/usr/bin/python

import re

npo12files = ['./jinek.htm', './midsomer.htm']
npo3files = ['./keuringsdienst.htm', './pownews.htm']

npo12regex = r"""<div class='span4'>\s*<div class='image-container'>\s*<a href="(.*?)">\s*(<div class="program-not-available">)?"""
npo3regex = r"""<div class='span4 image'>\s*<a href="(.*?)">\s*<div class="meta-container">\s*<div class="meta first">\s*<div class="md-label"><span class="npo-glyph triangle-right"></span></div>\s*<div class="md-value">.*?</div>\s*</div>\s*</div>\s*(<div class="program-not-available">)?"""

for filename in npo12files:
	with open(filename) as f:
		for match in re.finditer(npo12regex, f.read()):
			print(match.group(1), match.group(2) is None)
		print('')
		
for filename in npo3files:
	with open(filename) as f:
		for match in re.finditer(npo3regex, f.read()):
			print(match.group(1), match.group(2) is None)
		print('')