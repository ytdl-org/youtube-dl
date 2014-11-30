# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    ExtractorError,
)


class GoshgayIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)www.goshgay.com/video(?P<id>\d+?)($|/)'
    _TEST = {
        'url': 'http://www.goshgay.com/video4116282',
        'md5': '268b9f3c3229105c57859e166dd72b03',
        'info_dict': {
            'id': '4116282',
            'ext': 'flv',
            'title': 'md5:089833a4790b5e103285a07337f245bf',
            'thumbnail': 're:http://.*\.jpg',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        family_friendly = self._html_search_meta(
            'isFamilyFriendly', webpage, default='false')
        config_url = self._search_regex(
            r"'config'\s*:\s*'([^']+)'", webpage, 'config URL')

        config = self._download_xml(
            config_url, video_id, 'Downloading player config XML')

        if config is None:
            raise ExtractorError('Missing config XML')
        if config.tag != 'config':
            raise ExtractorError('Missing config attribute')
        fns = config.findall('file')
        if len(fns) < 1:
            raise ExtractorError('Missing media URI')
        video_url = fns[0].text

        url_comp = compat_urlparse.urlparse(url)
        ref = "%s://%s%s" % (url_comp[0], url_comp[1], url_comp[2])

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'http_referer': ref,
            'age_limit': 0 if family_friendly == 'true' else 18,
        }
