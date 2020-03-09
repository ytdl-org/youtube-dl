# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class sonumaIE(InfoExtractor):

	_VALID_URL=r'(?:https?://)?(?:www\.)?sonuma\.be/archive/[a-z-0-9]*'

	def _real_extract(self,url):
		video_id=self._match_id(url)
		webpage = self._download_webpage("https://www.sonuma.be/archive/"+video_id)
		title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')


		return{
		'id':video_id,
		'title':title,
		'description': self._og_search_description(webpage),
		}