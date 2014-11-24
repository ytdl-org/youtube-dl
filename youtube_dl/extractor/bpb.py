# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor

class BpbIE(InfoExtractor):
	IE_NAME = 'Bundeszentrale für politische Bildung'
	_VALID_URL = r'http://www\.bpb\.de/mediathek/.*'
	
	_TEST = {
		'url': 'http://www.bpb.de/mediathek/297/joachim-gauck-zu-1989-und-die-erinnerung-an-die-ddr',
		'md5': '0792086e8e2bfbac9cdf27835d5f2093',
		'info_dict': {
			'id': '12490',
			'ext': 'mp4',
			'title': 'Joachim Gauck zu 1989 und die Erinnerung an die DDR',
			'description': 'Joachim Gauck, erster Beauftragter für die Stasi-Unterlagen, spricht auf dem Geschichtsforum über die friedliche Revolution 1989 und eine "gewisse Traurigkeit" im Umgang mit der DDR-Vergangenheit.'
		}
	}
	
	def _real_extract(self, url):
		webpage = self._download_webpage(url, '')
		
		title = self._html_search_regex(r'<h2 class="white">(.*?)</h2>', webpage, 'title')
		
		video_id = self._html_search_regex(r'http://film\.bpb\.de/player/dokument_(?P<video_id>[0-9]+)\.mp4', webpage, 'video_id')
		
		url = 'http://film.bpb.de/player/dokument_' + video_id + '.mp4'
		
		description = self._og_search_description(webpage)
		
		return {
			'id': video_id,
			'url': url,
			'title': title,
			'description': description,
			'ext': 'mp4'
		}
