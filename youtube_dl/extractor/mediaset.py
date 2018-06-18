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
    ExtractorError
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
        'url': 'http://www.video.mediaset.it/video/matrix/full_chiambretti/puntata-del-25-maggio_846685.html',
        'md5': '1276f966ac423d16ba255ce867de073e',
        'info_dict': {
            'id': '846685',
            'ext': 'mp4',
            'title': 'Puntata del 25 maggio',
            'description': 'md5:ee2e456e3eb1dba5e814596655bb5296',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 6565,
            'creator': 'mediaset',
            'upload_date': '20180525',
            'series': 'Matrix',
            'categories': ['infotainment'],
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

        media_info = self._download_json(
            'https://www.video.mediaset.it/html/metainfo.sjson',
            video_id, 'Downloading media info', query={
                'id': video_id
            })['video']

        media_id = try_get(media_info, lambda x: x['guid']) or video_id

        video_list = self._download_json(
            'http://cdnsel01.mediaset.net/GetCdn2018.aspx',
            video_id, 'Downloading video CDN JSON', query={
                'streamid': media_id,
                'format': 'json',
            })['videoList']

        formats = []
        for format_url in video_list:
            if '.ism' in format_url:
                try:
                    formats.extend(self._extract_ism_formats(
                        format_url, video_id, ism_id='mss', fatal=False))
                except ExtractorError:
                    pass
            else:
                formats.append({
                    'url': format_url,
                    'format_id': determine_ext(format_url),
                })
        self._sort_formats(formats)

        title = media_info['title']

        creator = try_get(
            media_info, lambda x: x['brand-info']['publisher'], compat_str)
        category = try_get(
            media_info, lambda x: x['brand-info']['category'], compat_str)
        categories = [category] if category else None

        return {
            'id': video_id,
            'title': title,
            'description': media_info.get('short-description'),
            'thumbnail': media_info.get('thumbnail'),
            'duration': parse_duration(media_info.get('duration')),
            'creator': creator,
            'upload_date': unified_strdate(media_info.get('production-date')),
            'webpage_url': media_info.get('url'),
            'series': media_info.get('brand-value'),
            'categories': categories,
            'formats': formats,
        }
