# coding: utf-8
from __future__ import unicode_literals

import re

from ..utils import (
    bug_reports_message,
    JSON_LD_RE,
    merge_dicts,
    NO_DEFAULT,
    RegexNotFoundError,
    try_get,
    url_or_none,
)
from ..compat import compat_str

from .common import InfoExtractor


class MegaCartoonsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?megacartoons\.net/(?P<id>[a-zA-Z\d-]+)/'
    _TESTS = [{
        'url': 'https://www.megacartoons.net/help-wanted/',
        'md5': '4ba9be574f9a17abe0c074e2f955fded',
        'info_dict': {
            'id': 'help-wanted',
            'ext': 'mp4',
            'title': 'Help Wanted - SpongeBob SquarePants',
            'upload_date': '20200223',
            'timestamp': 1582416000,
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:2c909daa6c6cb16b2d4d791dd1a31632'
        }
    }, {
        'url': 'https://www.megacartoons.net/1000-years-of-courage/',
        'only_matching': True,
    }, {
        'url': 'https://www.megacartoons.net/911-2/',
        'only_matching': True,
    }]

    # adapted from common.py pending yt-dlp back-port
    def _search_json_ld(self, html, video_id, expected_type=None, **kwargs):
        json_ld_list = list(re.finditer(JSON_LD_RE, html))
        default = kwargs.get('default', NO_DEFAULT)
        fatal = kwargs.get('fatal', True) if default is NO_DEFAULT else False
        json_ld = []
        for mobj in json_ld_list:
            json_ld_item = self._parse_json(
                mobj.group('json_ld'), video_id, fatal=fatal)
            if not json_ld_item:
                continue
            if isinstance(json_ld_item, dict):
                json_ld.append(json_ld_item)
            elif isinstance(json_ld_item, (list, tuple)):
                json_ld.extend(json_ld_item)
        if json_ld:
            # handle initial '@graph' with one level of children
            if len(json_ld) > 0 and '@graph' in json_ld[0] and '@context' in json_ld[0]:
                # should always be hit here
                context = json_ld[0]['@context']
                json_ld_g = json_ld[0]['@graph'] or []
                for item in json_ld_g:
                    item.setdefault('@context', context)
                json_ld = json_ld_g + json_ld[1:]
            json_ld = self._json_ld(json_ld, video_id, fatal=fatal, expected_type=expected_type)
        if json_ld:
            return json_ld
        if default is not NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError('Unable to extract JSON-LD')
        else:
            self.report_warning('unable to extract JSON-LD %s' % bug_reports_message())
            return {}

    def _real_extract(self, url):
        # ID is equal to the episode name
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        info = self._search_json_ld(webpage, video_id, fatal=False) or {}

        info.update({
            'id': video_id,
            # Try to find a good title or fallback to the ID
            'title': info.get('title') or self._og_search_title(webpage) or video_id.replace('-', ' ').capitalize(),
        })

        if 'url' not in info or 'thumbnail' not in info:
            # Video data is stored in a json -> extract it from the raw html
            url_json = self._parse_json(self._html_search_regex(r'''<div\b[^>]+\bdata-item\s*=\s*(["'])(?P<videourls>\{.*})\1''', webpage, 'videourls', group='videourls', default='{}'), video_id, fatal=False) or {}

            video_url = url_or_none(try_get(url_json, lambda x: x['sources'][0]['src'], compat_str) or self._og_search_video_url(webpage))   # Get the video url
            video_thumbnail = url_or_none(url_json.get('splash') or self._og_search_thumbnail(webpage))            # Get the thumbnail
            info = merge_dicts(info, {
                'url': video_url,
                'thumbnail': video_thumbnail,
            })

        # Find the <article> class in the html
        article = self._search_regex(
            r'(?s)<article\b[^>]*?\bclass\s*=\s*[^>]*?\bpost\b[^>]*>(.+?)</article\b', webpage, 'post', default='')

        # Extract the actual description from it
        info['description'] = (
            self._html_search_regex(r'(?s)<p>\s*([^<]+)\s*</p>', article, 'videodescription', fatal=False)
            or self._og_search_description(webpage))

        return info
