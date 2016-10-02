# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    sanitized_Request,
    unified_strdate,
    urlencode_postdata,
    xpath_element,
    xpath_text,
)


class Laola1TvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?laola1\.tv/(?P<lang>[a-z]+)-(?P<portal>[a-z]+)/(?P<kind>[^/]+)/(?P<slug>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.laola1.tv/de-de/video/straubing-tigers-koelner-haie/227883.html',
        'info_dict': {
            'id': '227883',
            'display_id': 'straubing-tigers-koelner-haie',
            'ext': 'flv',
            'title': 'Straubing Tigers - Kölner Haie',
            'upload_date': '20140912',
            'is_live': False,
            'categories': ['Eishockey'],
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.laola1.tv/de-de/video/straubing-tigers-koelner-haie',
        'info_dict': {
            'id': '464602',
            'display_id': 'straubing-tigers-koelner-haie',
            'ext': 'flv',
            'title': 'Straubing Tigers - Kölner Haie',
            'upload_date': '20160129',
            'is_live': False,
            'categories': ['Eishockey'],
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.laola1.tv/de-de/livestream/2016-03-22-belogorie-belgorod-trentino-diatec-lde',
        'info_dict': {
            'id': '487850',
            'display_id': '2016-03-22-belogorie-belgorod-trentino-diatec-lde',
            'ext': 'flv',
            'title': 'Belogorie BELGOROD - TRENTINO Diatec',
            'upload_date': '20160322',
            'uploader': 'CEV - Europäischer Volleyball Verband',
            'is_live': True,
            'categories': ['Volleyball'],
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'This live stream has already finished.',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('slug')
        kind = mobj.group('kind')
        lang = mobj.group('lang')
        portal = mobj.group('portal')

        webpage = self._download_webpage(url, display_id)

        if 'Dieser Livestream ist bereits beendet.' in webpage:
            raise ExtractorError('This live stream has already finished.', expected=True)

        iframe_url = self._search_regex(
            r'<iframe[^>]*?id="videoplayer"[^>]*?src="([^"]+)"',
            webpage, 'iframe url')

        video_id = self._search_regex(
            r'videoid=(\d+)', iframe_url, 'video id')

        iframe = self._download_webpage(compat_urlparse.urljoin(
            url, iframe_url), display_id, 'Downloading iframe')

        partner_id = self._search_regex(
            r'partnerid\s*:\s*(["\'])(?P<partner_id>.+?)\1',
            iframe, 'partner id', group='partner_id')

        hd_doc = self._download_xml(
            'http://www.laola1.tv/server/hd_video.php?%s'
            % compat_urllib_parse_urlencode({
                'play': video_id,
                'partner': partner_id,
                'portal': portal,
                'lang': lang,
                'v5ident': '',
            }), display_id)

        _v = lambda x, **k: xpath_text(hd_doc, './/video/' + x, **k)
        title = _v('title', fatal=True)

        VS_TARGETS = {
            'video': '2',
            'livestream': '17',
        }

        req = sanitized_Request(
            'https://club.laola1.tv/sp/laola1/api/v3/user/session/premium/player/stream-access?%s' %
            compat_urllib_parse_urlencode({
                'videoId': video_id,
                'target': VS_TARGETS.get(kind, '2'),
                'label': _v('label'),
                'area': _v('area'),
            }),
            urlencode_postdata(
                dict((i, v) for i, v in enumerate(_v('req_liga_abos').split(',')))))

        token_url = self._download_json(req, display_id)['data']['stream-access'][0]
        token_doc = self._download_xml(token_url, display_id, 'Downloading token')

        token_attrib = xpath_element(token_doc, './/token').attrib
        token_auth = token_attrib['auth']

        if token_auth in ('blocked', 'restricted', 'error'):
            raise ExtractorError(
                'Token error: %s' % token_attrib['comment'], expected=True)

        formats = self._extract_f4m_formats(
            '%s?hdnea=%s&hdcore=3.2.0' % (token_attrib['url'], token_auth),
            video_id, f4m_id='hds')
        self._sort_formats(formats)

        categories_str = _v('meta_sports')
        categories = categories_str.split(',') if categories_str else []

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'upload_date': unified_strdate(_v('time_date')),
            'uploader': _v('meta_organisation'),
            'categories': categories,
            'is_live': _v('islive') == 'true',
            'formats': formats,
        }
