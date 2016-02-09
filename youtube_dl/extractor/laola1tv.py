# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    ExtractorError,
    sanitized_Request,
    xpath_element,
    xpath_text,
    unified_strdate,
    urlencode_postdata,
)


class Laola1TvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?laola1\.tv/(?P<lang>[a-z]+)-(?P<portal>[a-z]+)/.*?/(?P<slug>[\w-]+)'
    _TESTS = [{
        'url': 'http://www.laola1.tv/de-de/video/straubing-tigers-koelner-haie/227883.html',
        'info_dict': {
            'categories': ['Eishockey'],
            'ext': 'flv',
            'id': '227883',
            'is_live': False,
            'title': 'Straubing Tigers - Kölner Haie',
            'upload_date': '20140912',
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'http://www.laola1.tv/de-de/video/straubing-tigers-koelner-haie',
        'info_dict': {
            'categories': ['Eishockey'],
            'ext': 'flv',
            'id': '464602',
            'is_live': False,
            'title': 'Straubing Tigers - Kölner Haie',
            'upload_date': '20160129',
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        lang = mobj.group('lang')
        portal = mobj.group('portal')

        webpage = self._download_webpage(url, mobj.group('slug'))
        iframe_url = self._search_regex(
            r'<iframe[^>]*?id="videoplayer"[^>]*?src="([^"]+)"',
            webpage, 'iframe URL')

        video_id = self._search_regex(
            r'videoid=(\d+)', iframe_url, 'video ID')

        iframe = self._download_webpage(compat_urlparse.urljoin(
            url, iframe_url), video_id, note='Downloading iframe')

        partner_id = self._search_regex(
            r'partnerid\s*:\s*"([^"]+)"', iframe, 'partner ID')

        xml_url = ('http://www.laola1.tv/server/hd_video.php?' +
                   'play=%s&partner=%s&portal=%s&v5ident=&lang=%s' % (
                       video_id, partner_id, portal, lang))
        hd_doc = self._download_xml(xml_url, video_id)

        _v = lambda x, **k: xpath_text(hd_doc, './/video/' + x, **k)
        title = _v('title', fatal=True)

        categories = _v('meta_sports')
        if categories:
            categories = categories.split(',')

        time_date = _v('time_date')
        time_start = _v('time_start')
        upload_date = None
        if time_date and time_start:
            upload_date = unified_strdate(time_date + ' ' + time_start)

        json_url = ('https://club.laola1.tv/sp/laola1/api/v3/user/session' +
                    '/premium/player/stream-access?videoId=%s&target=2' +
                    '&label=laola1tv&area=%s') % (video_id, _v('area'))
        req = sanitized_Request(json_url, urlencode_postdata(
            dict((i, v) for i, v in enumerate(_v('req_liga_abos').split(',')))))

        token_url = self._download_json(req, video_id)['data']['stream-access'][0]
        token_doc = self._download_xml(
            token_url, video_id, note='Downloading token')

        token_attrib = xpath_element(token_doc, './/token').attrib
        token_auth = token_attrib['auth']

        if token_auth in ('blocked', 'restricted'):
            raise ExtractorError(
                'Token error: %s' % token_attrib['comment'], expected=True)

        video_url = '%s?hdnea=%s&hdcore=3.2.0' % (token_attrib['url'], token_auth)

        return {
            'categories': categories,
            'formats': self._extract_f4m_formats(
                video_url, video_id, f4m_id='hds'),
            'id': video_id,
            'is_live': _v('islive') == 'true',
            'title': title,
            'upload_date': upload_date,
            'uploader': _v('meta_organisation'),
        }
