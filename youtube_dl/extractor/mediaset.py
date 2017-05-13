# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    parse_duration,
    try_get,
    unified_strdate,
)


class MediasetIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    (?:
                        mediaset:|
                        https?://
                            (?:www\.)?video\.mediaset\.it/
                            (?:
                                (?:video|on-demand)/(?:[^/]+/)+[^/]+_|
                                player/playerIFrame(?:Twitter)?\.shtml\?.*?\bid=
                            )
                    )(?P<id>[0-9]+)
                    '''
    _TESTS = [{
        # full episode
        'url': 'http://www.video.mediaset.it/video/hello_goodbye/full/quarta-puntata_661824.html',
        'md5': '9b75534d42c44ecef7bf1ffeacb7f85d',
        'info_dict': {
            'id': '661824',
            'ext': 'mp4',
            'title': 'Quarta puntata',
            'description': 'md5:7183696d6df570e3412a5ef74b27c5e2',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1414,
            'creator': 'mediaset',
            'upload_date': '20161107',
            'series': 'Hello Goodbye',
            'categories': ['reality'],
        },
        'expected_warnings': ['is not a supported codec'],
    }, {
        # clip
        'url': 'http://www.video.mediaset.it/video/gogglebox/clip/un-grande-classico-della-commedia-sexy_661680.html',
        'only_matching': True,
    }, {
        # iframe simple
        'url': 'http://www.video.mediaset.it/player/playerIFrame.shtml?id=665924&autoplay=true',
        'only_matching': True,
    }, {
        # iframe twitter (from http://www.wittytv.it/se-prima-mi-fidavo-zero/)
        'url': 'https://www.video.mediaset.it/player/playerIFrameTwitter.shtml?id=665104&playrelated=false&autoplay=false&related=true&hidesocial=true',
        'only_matching': True,
    }, {
        'url': 'mediaset:661824',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [
            mobj.group('url')
            for mobj in re.finditer(
                r'<iframe\b[^>]+\bsrc=(["\'])(?P<url>https?://(?:www\.)?video\.mediaset\.it/player/playerIFrame(?:Twitter)?\.shtml\?.*?\bid=\d+.*?)\1',
                webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_list = self._download_json(
            'http://cdnsel01.mediaset.net/GetCdn.aspx',
            video_id, 'Downloading video CDN JSON', query={
                'streamid': video_id,
                'format': 'json',
            })['videoList']

        formats = []
        for format_url in video_list:
            if '.ism' in format_url:
                formats.extend(self._extract_ism_formats(
                    format_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': determine_ext(format_url),
                })
        self._sort_formats(formats)

        mediainfo = self._download_json(
            'http://plr.video.mediaset.it/html/metainfo.sjson',
            video_id, 'Downloading video info JSON', query={
                'id': video_id,
            })['video']

        title = mediainfo['title']

        creator = try_get(
            mediainfo, lambda x: x['brand-info']['publisher'], compat_str)
        category = try_get(
            mediainfo, lambda x: x['brand-info']['category'], compat_str)
        categories = [category] if category else None

        return {
            'id': video_id,
            'title': title,
            'description': mediainfo.get('short-description'),
            'thumbnail': mediainfo.get('thumbnail'),
            'duration': parse_duration(mediainfo.get('duration')),
            'creator': creator,
            'upload_date': unified_strdate(mediainfo.get('production-date')),
            'webpage_url': mediainfo.get('url'),
            'series': mediainfo.get('brand-value'),
            'categories': categories,
            'formats': formats,
        }
