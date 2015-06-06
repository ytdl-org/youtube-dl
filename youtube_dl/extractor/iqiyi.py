# coding: utf-8
from __future__ import unicode_literals

import hashlib
import math
import random
import re
import time
import uuid
import zlib

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import ExtractorError


class IqiyiIE(InfoExtractor):
    IE_NAME = 'iqiyi'

    _VALID_URL = r'http://(?:www\.)iqiyi.com/.+?\.html'

    _TEST = {
        'url': 'http://www.iqiyi.com/v_19rrojlavg.html',
        'md5': '2cb594dc2781e6c941a110d8f358118b',
        'info_dict': {
            'id': '9c1fb1b99d192b21c559e5a1a2cb3c73',
            'title': '美国德州空中惊现奇异云团 酷似UFO',
            'ext': 'f4v',
        }
    }

    def construct_video_urls(self, data, video_id, _uuid):
        def do_xor(x, y):
            a = y % 3
            if a == 1:
                return x ^ 121
            if a == 2:
                return x ^ 72
            return x ^ 103

        def get_encode_code(l):
            a = 0
            b = l.split('-')
            c = len(b)
            s = ''
            for i in range(c - 1, -1, -1):
                a = do_xor(int(b[c - i - 1], 16), i)
                s += chr(a)
            return s[::-1]

        def get_path_key(x, format_id, segment_index):
            mg = ')(*&^flash@#$%a'
            tm = self._download_json(
                'http://data.video.qiyi.com/t?tn=' + str(random.random()), video_id,
                note='Download path key of segment %d for format %s' % (segment_index + 1, format_id)
            )['t']
            t = str(int(math.floor(int(tm) / (600.0))))
            return hashlib.md5((t + mg + x).encode('utf8')).hexdigest()

        video_urls_dict = {}
        for format_item in data['vp']['tkl'][0]['vs']:
            if 0 < int(format_item['bid']) <= 10:
                format_id = self.get_format(format_item['bid'])
            else:
                continue

            video_urls = []

            video_urls_info = format_item['fs']
            if not format_item['fs'][0]['l'].startswith('/'):
                t = get_encode_code(format_item['fs'][0]['l'])
                if t.endswith('mp4'):
                    video_urls_info = format_item['flvs']

            for segment_index, segment in enumerate(video_urls_info):
                vl = segment['l']
                if not vl.startswith('/'):
                    vl = get_encode_code(vl)
                key = get_path_key(
                    vl.split('/')[-1].split('.')[0], format_id, segment_index)
                filesize = segment['b']
                base_url = data['vp']['du'].split('/')
                base_url.insert(-1, key)
                base_url = '/'.join(base_url)
                param = {
                    'su': _uuid,
                    'qyid': uuid.uuid4().hex,
                    'client': '',
                    'z': '',
                    'bt': '',
                    'ct': '',
                    'tn': str(int(time.time()))
                }
                api_video_url = base_url + vl + '?' + \
                    compat_urllib_parse.urlencode(param)
                js = self._download_json(
                    api_video_url, video_id,
                    note='Download video info of segment %d for format %s' % (segment_index + 1, format_id))
                video_url = js['l']
                video_urls.append(
                    (video_url, filesize))

            video_urls_dict[format_id] = video_urls
        return video_urls_dict

    def get_format(self, bid):
        _dict = {
            '1': 'h6',
            '2': 'h5',
            '3': 'h4',
            '4': 'h3',
            '5': 'h2',
            '10': 'h1'
        }
        return _dict.get(str(bid), None)

    def get_bid(self, format_id):
        _dict = {
            'h6': '1',
            'h5': '2',
            'h4': '3',
            'h3': '4',
            'h2': '5',
            'h1': '10',
            'best': 'best'
        }
        return _dict.get(format_id, None)

    def get_raw_data(self, tvid, video_id, enc_key, _uuid):
        tm = str(int(time.time()))
        param = {
            'key': 'fvip',
            'src': hashlib.md5(b'youtube-dl').hexdigest(),
            'tvId': tvid,
            'vid': video_id,
            'vinfo': 1,
            'tm': tm,
            'enc': hashlib.md5(
                (enc_key + tm + tvid).encode('utf8')).hexdigest(),
            'qyid': _uuid,
            'tn': random.random(),
            'um': 0,
            'authkey': hashlib.md5(
                (tm + tvid).encode('utf8')).hexdigest()
        }

        api_url = 'http://cache.video.qiyi.com/vms' + '?' + \
            compat_urllib_parse.urlencode(param)
        raw_data = self._download_json(api_url, video_id)
        return raw_data

    def get_enc_key(self, swf_url, video_id):
        req = self._request_webpage(
            swf_url, video_id, note='download swf content')
        cn = req.read()
        cn = zlib.decompress(cn[8:])
        pt = re.compile(b'MixerRemote\x08(?P<enc_key>.+?)\$&vv')
        enc_key = self._search_regex(pt, cn, 'enc_key').decode('utf8')
        return enc_key

    def _real_extract(self, url):
        webpage = self._download_webpage(
            url, 'temp_id', note='download video page')
        tvid = self._search_regex(
            r'data-player-tvid\s*=\s*[\'"](\d+)', webpage, 'tvid')
        video_id = self._search_regex(
            r'data-player-videoid\s*=\s*[\'"]([a-f\d]+)', webpage, 'video_id')
        swf_url = self._search_regex(
            r'(http://.+?MainPlayer.+?\.swf)', webpage, 'swf player URL')
        _uuid = uuid.uuid4().hex

        enc_key = self.get_enc_key(swf_url, video_id)

        raw_data = self.get_raw_data(tvid, video_id, enc_key, _uuid)

        if raw_data['code'] != 'A000000':
            raise ExtractorError('Unable to load data. Error code: ' + raw_data['code'])

        if not raw_data['data']['vp']['tkl']:
            raise ExtractorError('No support iQiqy VIP video')

        data = raw_data['data']

        title = data['vi']['vn']

        # generate video_urls_dict
        video_urls_dict = self.construct_video_urls(
            data, video_id, _uuid)

        # construct info
        entries = []
        for format_id in video_urls_dict:
            video_urls = video_urls_dict[format_id]
            for i, video_url_info in enumerate(video_urls):
                if len(entries) < i + 1:
                    entries.append({'formats': []})
                entries[i]['formats'].append(
                    {
                        'url': video_url_info[0],
                        'filesize': video_url_info[-1],
                        'format_id': format_id,
                        'preference': int(self.get_bid(format_id))
                    }
                )

        for i in range(len(entries)):
            self._sort_formats(entries[i]['formats'])
            entries[i].update(
                {
                    'id': '_part%d' % (i + 1),
                    'title': title,
                }
            )

        if len(entries) > 1:
            info = {
                '_type': 'multi_video',
                'id': video_id,
                'title': title,
                'entries': entries,
            }
        else:
            info = entries[0]
            info['id'] = video_id
            info['title'] = title

        return info
