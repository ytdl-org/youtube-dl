# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re
import datetime

class SexyKarmaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sexykarma\.com/gonewild/video/.+\-(?P<id>[a-zA-Z0-9\-]+)(.html)'
    _TESTS = [{
        'url': 'http://www.sexykarma.com/gonewild/video/taking-a-quick-pee-yHI70cOyIHt.html',
        'md5': 'b9798e7d1ef1765116a8f516c8091dbd',
        'info_dict': {
            'id': 'yHI70cOyIHt',
            'ext': 'mp4',
            'title': 'Taking a quick pee.',
            'uploader_id': 'wildginger7',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': int,
            'view_count': int,
            'upload_date': '20141007',
        }
    }, {
        'url': 'http://www.sexykarma.com/gonewild/video/pot-pixie-tribute-8Id6EZPbuHf.html',
        'md5': 'dd216c68d29b49b12842b9babe762a5d',
        'info_dict': {
            'id': '8Id6EZPbuHf',
            'ext': 'mp4',
            'title': 'pot_pixie tribute',
            'uploader_id': 'banffite',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': int,
            'view_count': int,
            'upload_date': '20141013',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
              
        title = self._html_search_regex(r'<h2 class="he2"><span>(.*?)</span>', webpage, 'title')
        uploader_id = self._html_search_regex(r'class="aupa">\n*(.*?)</a>', webpage, 'uploader')
        url = self._html_search_regex(r'<p><a href="(.*?)" ?\n*target="_blank"><font color', webpage, 'url')
        thumbnail = self._html_search_regex(r'<div id="player" style="z-index:1;"> <span id="edge"></span> <span id="container"><img[\n ]*src="(.+?)"', webpage, 'thumbnail')
        
        str_duration = self._html_search_regex(r'<tr>[\n\s]*<td>Time: </td>[\n\s]*<td align="right"><span>(.+)\n*', webpage, 'duration')
        duration = self._to_seconds(str_duration)

        str_views = self._html_search_regex(r'<tr>[\n\s]*<td>Views: </td>[\n\s]*<td align="right"><span>(.+)</span>', webpage, 'view_count')
        view_count = int(str_views)
        # print view_count

        date = self._html_search_regex(r'class="aup">Added: <strong>(.*?)</strong>', webpage, 'date')
        d = datetime.datetime.strptime(date, '%B %d, %Y')
        upload_date = d.strftime('%Y%m%d')

        return {
            'id': video_id,
            'title': title,
            'uploader_id': uploader_id,
            'url': url,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'upload_date': upload_date,
        }

    def _to_seconds(self, timestr):
        seconds= 0
        for part in timestr.split(':'):
            seconds= seconds*60 + int(part)
        return seconds
