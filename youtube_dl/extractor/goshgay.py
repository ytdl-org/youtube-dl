# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    str_to_int,
    ExtractorError,
)
import json


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
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._search_regex(r'class="video-title"><h1>(.+?)<', webpage, 'title')

        player_config = self._search_regex(
            r'(?s)jwplayer\("player"\)\.setup\(({.+?})\)', webpage, 'config settings')
        player_vars = json.loads(player_config.replace("'", '"'))
        width = str_to_int(player_vars.get('width'))
        height = str_to_int(player_vars.get('height'))
        config_uri = player_vars.get('config')

        if config_uri is None:
            raise ExtractorError('Missing config URI')
        node = self._download_xml(config_uri, video_id, 'Downloading player config XML',
                                  errnote='Unable to download XML')
        if node is None:
            raise ExtractorError('Missing config XML')
        if node.tag != 'config':
            raise ExtractorError('Missing config attribute')
        fns = node.findall('file')
        imgs = node.findall('image')
        if len(fns) != 1:
            raise ExtractorError('Missing media URI')
        video_url = fns[0].text
        if len(imgs) < 1:
            thumbnail = None
        else:
            thumbnail = imgs[0].text

        url_comp = compat_urlparse.urlparse(url)
        ref = "%s://%s%s" % (url_comp[0], url_comp[1], url_comp[2])

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'width': width,
            'height': height,
            'thumbnail': thumbnail,
            'http_referer': ref,
            'age_limit': 18,
        }
