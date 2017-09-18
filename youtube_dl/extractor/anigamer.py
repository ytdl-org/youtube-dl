# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import ExtractorError

import json
import math
import random
import re


class AnimeBahamutIE(InfoExtractor):
    _VALID_URL = r'https?://ani\.gamer\.com\.tw/animeVideo\.php\?sn=(?P<id>[0-9]+)'

    _ANI_BASE = 'https://ani.gamer.com.tw'
    _I2_BASE = 'https://i2.bahamut.com.tw'

    _TESTS = [{
        'url': 'https://ani.gamer.com.tw/animeVideo.php?sn=90',
        'info_dict': {
            'id': '90',
            'ext': 'mp4',
            'title': '冰菓[1]',
            'thumbnail': 'https://p2.bahamut.com.tw/B/2KU/11/0001306611.JPG',
            'description': '追求灰色校園生活的消極少年、與充滿好奇心又積極的少女在即將倒閉的古典社相遇了，他們的相遇是會帶來怎麼樣的青春生活呢？改編自米澤穗信古典社系列的同名原作《冰菓》，由京都動畫所製作的動畫作品《冰菓》已於今年春季開播。 這次《冰菓》的監督是擔任過《驚爆危機 校園篇》、《涼宮春日的消失》監督的 武本康弘。武本監'
        }
    }, {
        'url': 'https://ani.gamer.com.tw/animeVideo.php?sn=4243',
        'info_dict': {
            'id': '4243',
            'ext': 'mp4',
            'title': '無法掙脫的背叛[1]',
            'thumbnail': 'https://p2.bahamut.com.tw/B/2KU/26/0001309926.JPG',
            'description': '主角是在孤兒院長大的高中生「櫻井夕月」，而他擁有在觸碰人時能讀取他人記憶與思緒的特殊能力。某日，在他的面前出現了一位似曾相識、並讓他感到有點懷念的美貌青年「桀斯」，而桀斯也向夕月提出忠告，絕對不要在召喚死亡的紅月之夜「瓦爾波吉斯之夜」外出。 之後的某天，名為「祗王天白」的人拜訪了夕月，並告訴夕月他是'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        info = {'id': video_id}

        str_info = self._html_search_regex(r'<script[^>]+type="application/ld\+json"[^>]*>(?P<code>[^<]+)', webpage, 'code')
        video_info = json.loads(str_info)

        info['description'] = video_info[2].get('description')
        info['title'] = video_info[2].get('name')
        info['interaction_count'] = video_info[2].get('interactionCount')
        info['thumbnail'] = video_info[2].get('thumbnailUrl')

        if video_info[2].get('uploadDate'):
            dmoj = re.search(r'(?P<y>[0-9]+)-(?P<m>[0-9]+)-(?P<d>[0-9]+)T', video_info[2]['uploadDate'])
            info['upload_date'] = dmoj.group('y') + dmoj.group('m') + dmoj.group('d')

        device_id_json = self._download_json('%s/ajax/getdeviceid.php' % self._ANI_BASE, video_id,
                                        note='Getting device id', query={'id': ''})

        if device_id_json.get('deviceid'):
            device_id = device_id_json.get('deviceid')
        else:
            self.report_warning('Warning! Cannot get device id', video_id)

        ad_js = self._download_webpage('%s/JS/ad/animeVideo2.js' % self._I2_BASE, video_id, )

        minor_code = self._search_regex(r'var\s+getMinorAd\s*=\s*function\(\)\s*\{(?P<code>[^}]+)\};', ad_js, 'code')

        ad_list_s = self._search_regex(r'var\s+adlist\s*=\s*(?P<list>\[(.+?)\]);', minor_code, 'list')
        ad_list = json.loads(ad_list_s)
        del minor_code
        del ad_list_s

        ik = int(math.floor(9 * random.random()))

        ad_sid = ad_list[ik][2]
        ad_query = {
            's': ad_sid,
            'sn': video_id
        }
        self._download_webpage('%s/ajax/videoCastcishu.php' % self._ANI_BASE, video_id,
                                query=ad_query)

        ad_query['ad'] = 'end'
        self._download_webpage('%s/ajax/videoCastcishu.php' % self._ANI_BASE, video_id, query=ad_query)

        m3u8_query = {
            'sn': video_id,
            'device': device_id
        }

        m3u8_json = self._download_json('%s/ajax/m3u8.php' % self._ANI_BASE, video_id, query=m3u8_query)

        if 'error' in m3u8_json:
            raise ExtractorError('Cannot extract URL.')

        index_m3u8_url = m3u8_json.get('src')

        if index_m3u8_url[0:2] == '//':
            index_m3u8_url = 'https:' + index_m3u8_url

        formats = self._extract_m3u8_formats(index_m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native')

        info['formats'] = formats

        return info