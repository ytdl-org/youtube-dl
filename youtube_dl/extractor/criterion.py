# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    mimetype2ext,
    str_or_none,
    try_get,
    url_or_none,
)
from .vimeo import VimeoBaseInfoExtractor as VimeoBaseIE


class CriterionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?criterion\.com/films/(?P<id>\d+)-.+'
    _TESTS = [
        {
            'url': 'http://www.criterion.com/films/184-le-samourai',
            'info_dict': {
                'id': '265399901',
                'title': 'Le samouraï',
                'ext': 'mp4',
                'description': 'md5:56ad66935158c6c88d4e391397c00d22',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.criterion.com/films/28986-the-heiress',
            'info_dict': {
                'id': '315291282',
                'title': 'The Heiress',
                'ext': 'mp4',
                'description': 'md5:3d34fe5e6ff5520998b13137eba0f7ce',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.criterion.com/films/28836-funny-games',
            'info_dict': {
                'id': '316586307',
                'title': 'Funny Games',
                'ext': 'mp4',
                'description': 'md5:64326c0cd08a6a582c10d63349941250',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.criterion.com/films/613-the-magic-flute',
            'info_dict': {
                'id': '305845790',
                'title': 'The Magic Flute',
                'ext': 'mp4',
                'description': 'md5:9f232dcf15d9861c6a551662973482a5',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
    ]

    def _extract_embedded_url(self, pattern, html, group):
        return self._search_regex(pattern, html, 'embedded url', group=group)

    def _extract_formats_from_stream(self, data, final_id):
        ext_formats = []
        if isinstance(data, dict):
            cdns = data.get('cdns')
            if cdns:
                for cdn_name, cdn_data in cdns.items():
                    url = url_or_none(cdn_data.get('url'))

                    ext = determine_ext(url)

                    if ext == 'm3u8':
                        ext_formats.extend(
                            self._extract_m3u8_formats(
                                url,
                                final_id,
                                ext='mp4',
                                m3u8_id=str_or_none(cdn_name) or 'hls',
                                fatal=False,
                            )
                        )
                    # dash mpd
                    if ext == 'json':
                        ext_formats.extend(
                            self._extract_mpd_formats(
                                url.replace('master.json', 'master.mpd'),
                                final_id,
                                mpd_id=cdn_name,
                                fatal=False,
                            )
                        )
        return ext_formats

    def _extract_formats_from_other(self, src, data):
        if not isinstance(data, list):
            data = [data]
        ext_formats = []
        if src == 'progressive':
            for vid in data:
                profile = str_or_none(vid.get('profile'))
                ext_formats.append(
                    {
                        'url': url_or_none(vid.get('url')),
                        'ext': mimetype2ext(vid.get('mime')),
                        'format_id': vid.get('cdn') + (profile if profile else ''),
                        'height': int_or_none(vid.get('height')),
                        'width': int_or_none(vid.get('width')),
                        'fps': int_or_none(vid.get('fps')),
                    }
                )
                vid_id = vid.get('id') or ''
                self.to_screen('%s: Downloading mp4 information' % (vid_id,))
        return ext_formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=None) or self._html_search_meta(
            'twitter:title', webpage
        )
        description = self._og_search_description(
            webpage, default=None
        ) or self._html_search_meta('twitter:description', webpage, fatal=False)

        # Follow embedded url
        embedded_re = r'<iframe[^>]+?src=["\'](?P<url>https?:\/\/player\.vimeo\.com\/video\/(?P<id>\d+)\?[^"\']+?)["\']'
        embedded_id = str_or_none(
            self._extract_embedded_url(embedded_re, webpage, group='id')
        )
        embedded_url = url_or_none(
            self._extract_embedded_url(embedded_re, webpage, group='url')
        )

        embedded_webpage = self._download_webpage(
            embedded_url, embedded_id, headers={'Referer': url}
        )

        # Grab json data
        data_re = r'var\s*config\s*=\s*(?P<data>.*?);'
        data_str = self._search_regex(
            data_re, embedded_webpage, 'json data', group='data'
        )
        data = self._parse_json(data_str, embedded_id)

        final_id = str_or_none(try_get(data, lambda x: x['video']['id']))

        stream_types = ('hls', 'dash',)
        nonstream_types = ('progressive',)

        # Collect formats
        formats = []
        sources = try_get(data, lambda x: x['request']['files'], dict)
        if sources:
            for src, src_data in sources.items():
                if src in stream_types:
                    formats.extend(
                        self._extract_formats_from_stream(src_data, final_id)
                    )
                elif src in nonstream_types:
                    formats.extend(self._extract_formats_from_other(src, src_data))

            VimeoBaseIE._vimeo_sort_formats(self, formats)

        thumb_data = try_get(data, lambda x: x['video']['thumbs'], dict)
        thumbnails = []
        if thumb_data:
            for url in thumb_data:
                thumbnails.append({'url': url_or_none(thumb_data[url])})

        return {
            'id': final_id,
            'title': title,
            'description': description,
            'formats': formats,
            'thumbnails': thumbnails,
        }
