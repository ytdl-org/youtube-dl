# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re
import itertools
from ..utils import (
    int_or_none,
    js_to_json,
    parse_resolution,
    sanitize_url,
    update_url_query,
)


class CamWhoresBayVideoIE(InfoExtractor):
    IE_NAME = 'camwhoresbay:video'
    _VALID_URL = r'https?://(?:www\.)?camwhoresbay\.com/videos/(?P<id>[0-9]+)/.+'
    _TEST = {
        'url': 'https://www.camwhoresbay.com/videos/484472/kirsten-xxx-2022-01-19/',
        'md5': 'ae3c5c34866afbd062adf5d2321d66f3',
        'info_dict': {
            'id': '484472',
            'ext': 'mp4',
            'title': 'Kirsten_Xxx 2022-01-19',
            'uploader': '789sani',
            'url': r're:^https?://www\.camwhoresbay\.com/get_file/7/55259a27805bf1313318c14b2afb0dae1fef6e1dd4/484000/484472/484472_720p\.mp4/\?rnd=.+',
            'thumbnail': r're:^https?://cwbstatic.cdntrex.com/contents/videos_screenshots/484000/484472/preview_720p.mp4.jpg',
        }
    }

    @staticmethod
    def _parse_formats(flashvars):
        formats = []
        rnd = flashvars.get('rnd')
        for k, v in flashvars.items():
            if re.match(r'^video_(alt_)?url\d?$', k):
                f = {
                    'url': update_url_query(v, {'rnd': rnd, })
                }
                f.update(parse_resolution(flashvars.get(k + '_text')))
                formats.append(f)
        return formats

    @staticmethod
    def _parse_thumbnails(flashvars):
        thumbnails = []
        for k, v in flashvars.items():
            if re.match(r'^preview_url\d$', k):
                t = {
                    'url': sanitize_url(v),
                    'height': int_or_none(flashvars.get(k.replace('_url', '_height'))),
                }
                thumbnails.append(t)
        return thumbnails

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if re.search(r'(?s)<div class=\"no-player\"', webpage):
            print("Video is private, skipping.")
            return

        title = self._html_search_regex(r'<div class=\"headline\">\n\s*<h1>(.+?)</h1>', webpage, 'title')

        flashvars = self._parse_json(
            self._search_regex(r'(?s)var\s+flashvars\s*=\s*({.+?})\s*;', webpage, 'flashvars', default='{}'),
            video_id, transform_source=js_to_json)
        uploader = self._search_regex(r'''(?s)\bclass\s*=\s*["']avatar["'][^>]+?\btitle\s*=\s*["'](.+)["']''', webpage, 'uploader',
                                      fatal=False)

        formats = self._parse_formats(flashvars)
        thumbnails = self._parse_thumbnails(flashvars)

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'url': formats[0].get('url'),
            'formats': formats,
            'thumbnails': thumbnails,
        }


class CamWhoresBayModelIE(CamWhoresBayVideoIE):
    IE_NAME = 'camwhoresbay:model'
    _VALID_URL = r'https?://(?:www\.)?camwhoresbay\.com/models/(?P<id>[0-9a-z\-]+)/?'
    _MORE_PAGES_INDICATOR = r'''<li\s[^>]*\bclass\s*=\s*["']next["'][^>]*><a\s[^>]*href\s*=\s*["']#videos["']'''
    _TITLE = None
    _TITLE_RE = r'''(?is)<div\s[^>]+?\bclass\s*=\s*["']headline["'][^>]*>\s*<h1\s[^>]*>\s*(.*?)'s\s+New\s+Videos\b'''
    _BASE_URL_TEMPL = 'https://www.camwhoresbay.com/models/%s/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from='
    _TEST = {
        'url': 'https://www.camwhoresbay.com/models/kirsten-xxx/',
        'info_dict': {
            'id': 'kirsten-xxx',
            'title': 'Kirsten_xxx',
        }
    }
    _PAGE_SIZE = 35

    def _extract_list_title(self, webpage):
        return self._html_search_regex(
            self._TITLE_RE, webpage, 'list title', fatal=False)

    def _title_and_entries(self, model_id, base_url):
        for page in itertools.count(1):
            webpage = self._download_webpage('%s%d' % (base_url, page), model_id, 'Downloading page %s' % page)

            if page == 1:
                yield self._extract_list_title(webpage)

            for video_id in re.findall(
                    r'(?is)<div\s[^>]*\bclass\s*=\s*["\'.*?\bvideo\-item\b.*?["\'][^>]*>\s*<a\s[^>]*\bhref\s*=\s*["\'](.*?)["\']',
                    webpage):
                yield self.url_result(video_id)

            if re.search(self._MORE_PAGES_INDICATOR, webpage, re.DOTALL) is None:
                break

    def _extract_videos(self, list_id, base_url):
        title_and_entries = self._title_and_entries(list_id, base_url)
        list_title = next(title_and_entries)
        return self.playlist_result(title_and_entries, list_id, list_title)

    def _real_extract(self, url):
        model_id = self._match_id(url)
        return self._extract_videos(model_id, self._BASE_URL_TEMPL % (model_id,))
