# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class sonumaIE(InfoExtractor):

	_VALID_URL=r'(?:https?://)?(?:www\.)?sonuma\.be/archive/'

	def _real_extract(self,url):
		video_id=self._match_id(url)
		webpage = self._download_webpage("https://www.sonuma.be/archive/%s/"video_id , video_id)
		title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')

		download_url=self._html_search_regex(
			r'https://vod.infomaniak.com/redirect/sonumasa_2_vod/web2-39166/copy-32/d611823b-d693-29b6-e040-010a07647b9b.mp4?sKey=2faa94b1da19002ca8b8abe944a7ecc8',webpage,"title")
		return{
		'id':video_id,
		'title':title,
		'description': self._og_search_description(webpage),
		}
