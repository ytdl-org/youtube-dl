# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re
import itertools
from ..utils import (
    js_to_json,
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
            'url': r're:https://www\.camwhoresbay\.com/get_file/7/55259a27805bf1313318c14b2afb0dae1fef6e1dd4/484000/484472/484472_720p\.mp4/\?rnd=.+',
            # 'formats': [{
            #     'url': r're:https://www\.camwhoresbay\.com/get_file/7/55259a27805bf1313318c14b2afb0dae1fef6e1dd4/484000/484472/484472\.mp4/\?rnd=.+',
            #     'height': 360
            # }, {
            #     'url': r're:https://www\.camwhoresbay\.com/get_file/7/55259a27805bf1313318c14b2afb0dae1fef6e1dd4/484000/484472/484472_480p\.mp4/\?rnd=.+',
            #     'height': 480
            # }, {
            #     'url': r're:https://www\.camwhoresbay\.com/get_file/7/55259a27805bf1313318c14b2afb0dae1fef6e1dd4/484000/484472/484472_720p\.mp4/\?rnd=.+',
            #     'height': 720
            # }]
            'thumbnails': [{
                'url': 'https://cwbstatic.cdntrex.com/contents/videos_screenshots/484000/484472/preview.mp4.jpg',
                'height': 360
            }, {
                'url': 'https://cwbstatic.cdntrex.com/contents/videos_screenshots/484000/484472/preview_480p.mp4.jpg',
                'height': 480
            }, {
                'url': 'https://cwbstatic.cdntrex.com/contents/videos_screenshots/484000/484472/preview_720p.mp4.jpg',
                'height': 720
            }],
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    @staticmethod
    def _parse_formats(flashvars):
        formats = []
        rnd = flashvars.get('rnd')
        for k, v in flashvars.items():
            if re.match(r"^video_(alt_)?url\d?$", k):
                f = {
                    'url': '{}?rnd={}'.format(v, rnd),
                    'height': int(flashvars['{}_text'.format(k)][:-1])
                }
                formats.append(f)
        return formats

    @staticmethod
    def _parse_thumbnails(flashvars):
        thumbnails = []
        for k, v in flashvars.items():
            if re.match(r"^preview_url\d$", k):
                t = {
                    'url': 'https:{}'.format(v),
                    'height': int(flashvars[k.replace('_url', '_height')])
                }
                thumbnails.append(t)
        return thumbnails

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<div class=\"headline\">\n\s*<h1>(.+?)</h1>', webpage, 'title')

        flashvars = self._parse_json(
            self._search_regex(r'var\s+flashvars\s+=\s+({\n.+});', webpage, 'flashvars', default='{}'),
            video_id, transform_source=js_to_json)
        uploader = self._search_regex(r'class=\"avatar\" href=\"http.+/\" title=\"(.+)\"', webpage, 'uploader',
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
    _MORE_PAGES_INDICATOR = r'<li\s+class="next"><a\s+href="#videos"'
    _TITLE = None
    _TITLE_RE = r'<div\s+class=\"headline\">\n\s*<h1>\s*(.*?)\'s New Videos.+</h1>'
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
        return self._TITLE or self._html_search_regex(
            self._TITLE_RE, webpage, 'list title', fatal=False)

    def _title_and_entries(self, model_id, base_url):
        for page in itertools.count(1):
            webpage = self._download_webpage('%s%d' % (base_url, page), model_id, 'Downloading page %s' % page)

            if page == 1:
                yield self._extract_list_title(webpage)

            for video_id in re.findall(r'<div\s+class=\"video-item\s*\">\n\s*<a href=\"(.*?)\"\s+title', webpage):
                yield self.url_result(video_id)

            if re.search(self._MORE_PAGES_INDICATOR, webpage, re.DOTALL) is None:
                break

    def _extract_videos(self, list_id, base_url):
        title_and_entries = self._title_and_entries(list_id, base_url)
        list_title = next(title_and_entries)
        return self.playlist_result(title_and_entries, list_id, list_title)

    def _real_extract(self, url):
        model_id = self._match_id(url)
        return self._extract_videos(model_id, self._BASE_URL_TEMPL % model_id)
