# coding: utf-8
from __future__ import unicode_literals

import re
from datetime import datetime

from ..utils import get_element_by_class
from .common import InfoExtractor

test_partial = {
    'md5': 'fe63bb94879189bd9ff7420d0b187352',
    'info_dict': {
        'artist': 'mothy_悪ノＰ',
        'description': '悪ノ娘のアレンジバージョンです。',
        'ext': 'mp3',
        'id': 'es7uj48x6bvcbtgy',
        'thumbnail': r're:https?://c1\.piapro\.jp/timg/nogoc3x8d4m0j416_20080819185021_0180_1440\.jpg',
        'timestamp': 1263600322,
        'title': '悪ノ娘～velvet mix～',
        'upload_date': '20100116',
        'uploader': 'mothy_悪ノＰ',
        'uploader_url': r're:https?://piapro\.jp/mothy',
        'url': 'https://cdn.piapro.jp/mp3_a/es/es7uj48x6bvcbtgy_20100116020522_audition.mp3',
    }
}


class PiaproIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?piapro\.jp/(conten)?t/(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [dict({'url': 'http://piapro.jp/t/KToM'}, **test_partial),
              dict({'url': 'http://piapro.jp/content/es7uj48x6bvcbtgy'}, **test_partial)]

    def _real_extract(self, url):
        url_id = self._match_id(url)
        webpage = self._download_webpage(url, url_id)

        if re.search(r'/content/([0-9a-zA-Z]+)', url):
            content_id = url_id
        else:
            content_id = self._search_regex(r'''contentId\s*:\s*['"]([0-9a-zA-Z]+?)['\"]''', webpage, 'content_id')

        create_date_str = self._search_regex(r'''createDate\s*:\s*['"]([0-9]{14})['"]''', webpage, 'create_date', fatal=False) or \
            self._search_regex(r'''["']https?://songle\.jp/songs/piapro\.jp.*([0-9]{14})['"]''', webpage, 'create_date')
        create_date = datetime.strptime(create_date_str, '%Y%m%d%H%M%S')
        create_date_unix = (create_date - datetime(1970,1,1)).total_seconds()

        uploader = get_element_by_class("cd_user-name", webpage)
        try:
            uploader_without_honorific = re.match('.+(?=さん)', uploader).group(0)
        except IndexError:
            uploader_without_honorific = None
        except AttributeError:
            uploader_without_honorific = uploader

        return {
            'artist':       uploader_without_honorific or uploader,
            'description':  get_element_by_class("cd_dtl_cap", webpage),
            'id':           content_id,
            'thumbnail':    self._search_regex(r'(https?://c1\.piapro\.jp/timg/.+?_1440\.jpg)', webpage, 'thumbnail', fatal=False),
            'timestamp':    create_date_unix,
            'title':        get_element_by_class("works-title", webpage) or self._html_search_regex(r'<title>[^<]*「(.*?)」<', webpage, 'title', fatal=False),
            'uploader':     uploader_without_honorific or uploader,
            # 'uploader_url': self._search_regex(r'<a\s+.*?href="(https?://piapro\.jp/.+?)"', cls_userbar_name, 'uploader_url', fatal=False),  # FIXME
            'url':          'http://cdn.piapro.jp/mp3_a/{}/{}_{}_audition.mp3'.format(content_id[:2], content_id, create_date_str)
        }
