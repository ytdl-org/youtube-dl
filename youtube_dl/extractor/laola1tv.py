from __future__ import unicode_literals

import random
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class Laola1TvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?laola1\.tv/(?P<lang>[a-z]+)-(?P<portal>[a-z]+)/.*?/(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.laola1.tv/de-de/live/bwf-bitburger-open-grand-prix-gold-court-1/250019.html',
        'info_dict': {
            'id': '250019',
            'ext': 'mp4',
            'title': 'Bitburger Open Grand Prix Gold - Court 1',
            'categories': ['Badminton'],
            'uploader': 'BWF - Badminton World Federation',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }

    _BROKEN = True  # Not really - extractor works fine, but f4m downloader does not support live streams yet.

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

        xml_url = ('http://www.laola1.tv/server/hd_video.php?' +
                   'play=%s&partner=1&portal=%s&v5ident=&lang=%s' % (
                       video_id, portal, lang))
        hd_doc = self._download_xml(xml_url, video_id)

        title = hd_doc.find('.//video/title').text
        flash_url = hd_doc.find('.//video/url').text
        categories = hd_doc.find('.//video/meta_sports').text.split(',')
        uploader = hd_doc.find('.//video/meta_organistation').text

        ident = random.randint(10000000, 99999999)
        token_url = '%s&ident=%s&klub=0&unikey=0&timestamp=%s&auth=%s' % (
            flash_url, ident, flashvars['timestamp'], flashvars['auth'])

        token_doc = self._download_xml(
            token_url, video_id, note='Downloading token')
        token_attrib = token_doc.find('.//token').attrib
        if token_attrib.get('auth') == 'blocked':
            raise ExtractorError('Token error: ' % token_attrib.get('comment'))

        video_url = '%s?hdnea=%s&hdcore=3.2.0' % (
            token_attrib['url'], token_attrib['auth'])

        return {
            'id': video_id,
            'is_live': True,
            'title': title,
            'url': video_url,
            'uploader': uploader,
            'categories': categories,
            'ext': 'mp4',
        }
