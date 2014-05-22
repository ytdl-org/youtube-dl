# encoding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class CinemassacreIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?cinemassacre\.com/(?P<date_Y>[0-9]{4})/(?P<date_m>[0-9]{2})/(?P<date_d>[0-9]{2})/(?P<display_id>[^?#/]+)'
    _TESTS = [
        {
            'url': 'http://cinemassacre.com/2012/11/10/avgn-the-movie-trailer/',
            'file': '19911.mp4',
            'md5': 'fde81fbafaee331785f58cd6c0d46190',
            'info_dict': {
                'upload_date': '20121110',
                'title': '“Angry Video Game Nerd: The Movie” – Trailer',
                'description': 'md5:fb87405fcb42a331742a0dce2708560b',
            },
        },
        {
            'url': 'http://cinemassacre.com/2013/10/02/the-mummys-hand-1940',
            'file': '521be8ef82b16.mp4',
            'md5': 'd72f10cd39eac4215048f62ab477a511',
            'info_dict': {
                'upload_date': '20131002',
                'title': 'The Mummy’s Hand (1940)',
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)
        video_date = mobj.group('date_Y') + mobj.group('date_m') + mobj.group('date_d')
        mobj = re.search(r'src="(?P<embed_url>http://player\.screenwavemedia\.com/play/[a-zA-Z]+\.php\?id=(?:Cinemassacre-)?(?P<video_id>.+?))"', webpage)
        if not mobj:
            raise ExtractorError('Can\'t extract embed url and video id')
        playerdata_url = mobj.group('embed_url')
        video_id = mobj.group('video_id')

        video_title = self._html_search_regex(
            r'<title>(?P<title>.+?)\|', webpage, 'title')
        video_description = self._html_search_regex(
            r'<div class="entry-content">(?P<description>.+?)</div>',
            webpage, 'description', flags=re.DOTALL, fatal=False)

        playerdata = self._download_webpage(playerdata_url, video_id)
        video_thumbnail = self._search_regex(r'image: \'(?P<thumbnail>[^\']+)\'', playerdata, 'thumbnail', fatal=False)
        sd_url = self._search_regex(r'file: \'([^\']+)\', label: \'SD\'', playerdata, 'sd_file')
        videolist_url = self._search_regex(r'file: \'([^\']+\.smil)\'}', playerdata, 'videolist_url')
        
        videolist = self._download_webpage(videolist_url, video_id)
        formats = []
        baseurl = sd_url[:sd_url.rfind('/')+1]
        for match in re.finditer('<video src="mp4:(?P<file>[^"]+_(?P<format_id>[^"]+)\.[^"]+)" system-bitrate="(?P<br>\d+)"(?: width="(?P<width>\d+)" height="(?P<height>\d+)")?/>', videolist):
            format = {
                'url': baseurl + match.group('file'),
                'format_id': match.group('format_id')
            }
            if match.group('width'):
                format.update({
                    'tbr': int(match.group('br')) // 1000,
                    'width': int(match.group('width')),
                    'height': int(match.group('height'))
                })
            else:
                format.update({
                    'abr': int(match.group('br')) // 1000,
                    'vcodec': 'none'
                })
            formats.append(format)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail': video_thumbnail,
        }
