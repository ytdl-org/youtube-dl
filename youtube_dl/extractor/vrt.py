# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    float_or_none,
)


class VRTIE(InfoExtractor):
    IE_DESC = 'vrt.be, sporza.be'
    _VALID_URL = r'https?://(?:www\.)?(?:vrt|sporza)\.be/(?!(?:vrtnu))(?:[^/]+/)+(?P<id>[^/]+)/*'
    _TESTS = [
        # vrt.be
        {
            'url': 'https://www.vrt.be/vrtnws/nl/2019/03/29/cyberbeveiliging-164-studenten-nemen-deel-aan-wedstrijd-die-oo/',
            'md5': 'b965693d0cb2c7ca5c0acbecd15d9442',
            'info_dict': {
                'id': 'vid-c65417a1-c725-47b2-8692-4c77234119cd',
                'ext': 'mp4',
                'title': 'Cyberbeveiliging - 164 studenten nemen deel aan wedstrijd, die ook een soort jobbeurs is',
                'description': 'Het tekort aan computerwetenschappers is een oud zeer. Voor hen zijn er zo maar eventjes 16.000 vacatures.',
                'duration': 88.19,
            },
            'skip': 'HTTP Error 404: Not Found',
        },
        # sporza.be
        {
            'url': 'https://sporza.be/nl/2019/03/31/sterke-alexander-kristoff-wint-gent-wevelgem-in-de-sprint/',
            'md5': 'fb5eb1716e2d451d5f3abcf3c9fcab58',
            'info_dict': {
                'id': 'vid-0eb67979-227a-42b0-ab6d-1a5836779d7e',
                'ext': 'mp4',
                'title': 'Sterke Alexander Kristoff wint Gent-Wevelgem in de sprint',
                'description': '...',
                'duration': 334.05,
            },
            'skip': 'HTTP Error 404: Not Found',
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'data-videoid="([^"]+)"', webpage, 'video id')

        publication_id = self._search_regex(
            r'data-publicationid="([^"]+)"', webpage, 'publication id')

        media_url = self._search_regex(
            r'data-mediaapiurl="([^"]+)"', webpage, 'media url')

        client = self._search_regex(
            r'data-client="([^"]+)"', webpage, 'client')

        headers = {'Content-Type': 'application/json'}
        result = self._download_json(
            '%s/tokens' % (media_url), video_id,
            'Downloading player token',
            headers=headers, data={})

        vrtPlayerToken = result['vrtPlayerToken']

        formats = []

        targetUrls = self._download_json(
            '%s/videos/%s$%s?vrtPlayerToken=%s&client=%s' % (media_url, publication_id, video_id, vrtPlayerToken, client),
            video_id,
            'Downloading target url data',
            headers=headers)

        for t in targetUrls['targetUrls']:
            if '.m3u8' in t['url']:
                formats.extend(self._extract_m3u8_formats(t['url'], video_id))
            elif '.mpd' in t['url']:
                formats.extend(self._extract_mpd_formats(t['url'], video_id))

        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = float_or_none(self._search_regex(
            r'data-video-sitestat-pubdate="(\d+)"', webpage, 'timestamp', fatal=False), 1000)
        duration = float_or_none(self._search_regex(
            r'data-duration="(\d+)"', webpage, 'duration', fatal=False), 1000)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }
