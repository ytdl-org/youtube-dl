# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    get_element_by_id,
)


class MorningstarIE(InfoExtractor):
    IE_DESC = 'morningstar.com'
    _VALID_URL = r'https?://(?:www\.)?morningstar\.com/[cC]over/video[cC]enter\.aspx\?id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.morningstar.com/cover/videocenter.aspx?id=615869',
        'md5': '6c0acface7a787aadc8391e4bbf7b0f5',
        'info_dict': {
            'id': '615869',
            'ext': 'mp4',
            'title': 'Get Ahead of the Curve on 2013 Taxes',
            'description': 'md5:0f71dedfd54bb3dca09e6474e2b624f7',
            'thumbnail': r're:^https?://.*m(?:orning)?star\.com/.+thumb\.jpg$'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        title = get_element_by_id('titleLink', webpage)
        if not title:
            raise ExtractorError('Unable to extract title for %s.' % video_id)

        video_url = self._html_search_regex(
            r'<input type="hidden" id="hidVideoUrl" value="([^"]+)"',
            webpage, 'video URL')
        thumbnail = self._html_search_regex(
            r'<input type="hidden" id="hidSnapshot" value="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'description': get_element_by_id('mstarDeck', webpage),
        }
