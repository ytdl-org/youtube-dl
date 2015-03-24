# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    xpath_text,
)


class Laola1TvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?laola1\.tv/(?P<lang>[a-z]+)-(?P<portal>[a-z]+)/.*?/(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.laola1.tv/de-de/video/straubing-tigers-koelner-haie/227883.html',
        'info_dict': {
            'id': '227883',
            'ext': 'mp4',
            'title': 'Straubing Tigers - Kölner Haie',
            'categories': ['Eishockey'],
            'is_live': False,
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        lang = mobj.group('lang')
        portal = mobj.group('portal')

        webpage = self._download_webpage(url, video_id)
        iframe_url = self._search_regex(
            r'<iframe[^>]*?class="main_tv_player"[^>]*?src="([^"]+)"',
            webpage, 'iframe URL')

        iframe = self._download_webpage(
            iframe_url, video_id, note='Downloading iframe')
        flashvars_m = re.findall(
            r'flashvars\.([_a-zA-Z0-9]+)\s*=\s*"([^"]*)";', iframe)
        flashvars = dict((m[0], m[1]) for m in flashvars_m)

        partner_id = self._search_regex(
            r'partnerid\s*:\s*"([^"]+)"', iframe, 'partner id')

        xml_url = ('http://www.laola1.tv/server/hd_video.php?' +
                   'play=%s&partner=%s&portal=%s&v5ident=&lang=%s' % (
                       video_id, partner_id, portal, lang))
        hd_doc = self._download_xml(xml_url, video_id)

        title = xpath_text(hd_doc, './/video/title', fatal=True)
        flash_url = xpath_text(hd_doc, './/video/url', fatal=True)
        uploader = xpath_text(hd_doc, './/video/meta_organistation')
        is_live = xpath_text(hd_doc, './/video/islive') == 'true'

        categories = xpath_text(hd_doc, './/video/meta_sports')
        if categories:
            categories = categories.split(',')

        ident = random.randint(10000000, 99999999)
        token_url = '%s&ident=%s&klub=0&unikey=0&timestamp=%s&auth=%s' % (
            flash_url, ident, flashvars['timestamp'], flashvars['auth'])

        token_doc = self._download_xml(
            token_url, video_id, note='Downloading token')
        token_attrib = token_doc.find('.//token').attrib
        if token_attrib.get('auth') in ('blocked', 'restricted'):
            raise ExtractorError(
                'Token error: %s' % token_attrib.get('comment'), expected=True)

        video_url = '%s?hdnea=%s&hdcore=3.2.0' % (
            token_attrib['url'], token_attrib['auth'])

        return {
            'id': video_id,
            'is_live': is_live,
            'title': title,
            'url': video_url,
            'uploader': uploader,
            'categories': categories,
            'ext': 'mp4',
        }
