# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)


class CinemassacreIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?cinemassacre\.com/(?P<date_Y>[0-9]{4})/(?P<date_m>[0-9]{2})/(?P<date_d>[0-9]{2})/(?P<display_id>[^?#/]+)'
    _TESTS = [
        {
            'url': 'http://cinemassacre.com/2012/11/10/avgn-the-movie-trailer/',
            'md5': 'fde81fbafaee331785f58cd6c0d46190',
            'info_dict': {
                'id': '19911',
                'ext': 'mp4',
                'upload_date': '20121110',
                'title': '“Angry Video Game Nerd: The Movie” – Trailer',
                'description': 'md5:fb87405fcb42a331742a0dce2708560b',
            },
        },
        {
            'url': 'http://cinemassacre.com/2013/10/02/the-mummys-hand-1940',
            'md5': 'd72f10cd39eac4215048f62ab477a511',
            'info_dict': {
                'id': '521be8ef82b16',
                'ext': 'mp4',
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

        playerdata = self._download_webpage(playerdata_url, video_id, 'Downloading player webpage')
        video_thumbnail = self._search_regex(
            r'image: \'(?P<thumbnail>[^\']+)\'', playerdata, 'thumbnail', fatal=False)
        sd_url = self._search_regex(r'file: \'([^\']+)\', label: \'SD\'', playerdata, 'sd_file')
        videolist_url = self._search_regex(r'file: \'([^\']+\.smil)\'}', playerdata, 'videolist_url')

        videolist = self._download_xml(videolist_url, video_id, 'Downloading videolist XML')

        formats = []
        baseurl = sd_url[:sd_url.rfind('/')+1]
        for video in videolist.findall('.//video'):
            src = video.get('src')
            if not src:
                continue
            file_ = src.partition(':')[-1]
            width = int_or_none(video.get('width'))
            height = int_or_none(video.get('height'))
            bitrate = int_or_none(video.get('system-bitrate'))
            format = {
                'url': baseurl + file_,
                'format_id': src.rpartition('.')[0].rpartition('_')[-1],
            }
            if width or height:
                format.update({
                    'tbr': bitrate // 1000 if bitrate else None,
                    'width': width,
                    'height': height,
                })
            else:
                format.update({
                    'abr': bitrate // 1000 if bitrate else None,
                    'vcodec': 'none',
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
