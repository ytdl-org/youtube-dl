# coding: utf-8
from __future__ import unicode_literals

import hashlib
import math
import random
import time
import uuid
import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    ExtractorError,
    int_or_none,
)


class IqiyiIE(InfoExtractor):
    IE_NAME = 'iqiyi'
    IE_DESC = '爱奇艺'

    _VALID_URL = r'http://(?:[^.]+\.)?iqiyi\.com/.+\.html'

    _TESTS = [{
        'url': 'http://www.iqiyi.com/v_19rrojlavg.html',
        'md5': '2cb594dc2781e6c941a110d8f358118b',
        'info_dict': {
            'id': '9c1fb1b99d192b21c559e5a1a2cb3c73',
            'title': '美国德州空中惊现奇异云团 酷似UFO',
            'ext': 'f4v',
        }
    }, {
        'url': 'http://www.iqiyi.com/v_19rrhnnclk.html',
        'info_dict': {
            'id': 'e3f585b550a280af23c98b6cb2be19fb',
            'title': '名侦探柯南第752集',
        },
        'playlist': [{
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part1',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part2',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part3',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part4',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part5',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part6',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part7',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part8',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }],
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.iqiyi.com/w_19rt6o8t9p.html',
        'only_matching': True,
    }, {
        'url': 'http://www.iqiyi.com/a_19rrhbc6kt.html',
        'only_matching': True,
    }, {
        'url': 'http://yule.iqiyi.com/pcb.html',
        'only_matching': True,
    }]

    _FORMATS_MAP = [
        ('1', 'h6'),
        ('2', 'h5'),
        ('3', 'h4'),
        ('4', 'h3'),
        ('5', 'h2'),
        ('10', 'h1'),
    ]

    @staticmethod
    def md5_text(text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def construct_formats(self, data, video_id, _uuid):
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
            return self.md5_text(t + mg + x)

        formats = []
        for format_item in data['vp']['tkl'][0]['vs']:
            if 0 < int(format_item['bid']) <= 10:
                format_id = self.get_format(format_item['bid'])
            else:
                continue

            parts = []

            video_urls_info = format_item['fs']
            if not format_item['fs'][0]['l'].startswith('/'):
                t = get_encode_code(format_item['fs'][0]['l'])
                if t.endswith('mp4'):
                    video_urls_info = format_item['flvs']

            for part_index, part in enumerate(video_urls_info):
                vl = part['l']
                if not vl.startswith('/'):
                    vl = get_encode_code(vl)
                key = get_path_key(
                    vl.split('/')[-1].split('.')[0], format_id, part_index)
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
                    note='Download video info of part %d for format %s' % (part_index + 1, format_id))
                video_url = js['l']
                parts.append({
                    'url': video_url,
                    'filesize': int_or_none(part['b']),
                })

            format_info = {
                'format_id': format_id,
                'parts': parts,
                'duration': int_or_none(format_item.get('duration')),
            }
            scrsz = format_item.get('scrsz')
            if scrsz:
                mobj = re.match(r'(\d+)x(\d+)', scrsz)
                if mobj:
                    format_info.update({
                        'width': int(mobj.group(1)),
                        'height': int(mobj.group(2)),
                    })
            formats.append(format_info)
        self._sort_formats(formats)
        return formats

    def get_format(self, bid):
        matched_format_ids = [_format_id for _bid, _format_id in self._FORMATS_MAP if _bid == str(bid)]
        return matched_format_ids[0] if len(matched_format_ids) else None

    def get_bid(self, format_id):
        matched_bids = [_bid for _bid, _format_id in self._FORMATS_MAP if _format_id == format_id]
        return matched_bids[0] if len(matched_bids) else None

    def get_raw_data(self, tvid, video_id, enc_key, _uuid):
        tm = str(int(time.time()))
        tail = tm + tvid
        param = {
            'key': 'fvip',
            'src': self.md5_text('youtube-dl'),
            'tvId': tvid,
            'vid': video_id,
            'vinfo': 1,
            'tm': tm,
            'enc': self.md5_text(enc_key + tail),
            'qyid': _uuid,
            'tn': random.random(),
            'um': 0,
            'authkey': self.md5_text(self.md5_text('') + tail),
        }

        api_url = 'http://cache.video.qiyi.com/vms' + '?' + \
            compat_urllib_parse.urlencode(param)
        raw_data = self._download_json(api_url, video_id)
        return raw_data

    def get_enc_key(self, swf_url, video_id):
        # TODO: automatic key extraction
        # last update at 2015-12-18 for Zombie::bite
        enc_key = '8b6b683780897eb8d9a48a02ccc4817d'[::-1]
        return enc_key

    def _real_extract(self, url):
        webpage = self._download_webpage(
            url, 'temp_id', note='download video page')
        tvid = self._search_regex(
            r'data-player-tvid\s*=\s*[\'"](\d+)', webpage, 'tvid')
        video_id = self._search_regex(
            r'data-player-videoid\s*=\s*[\'"]([a-f\d]+)', webpage, 'video_id')
        swf_url = self._search_regex(
            r'(http://[^\'"]+MainPlayer[^.]+\.swf)', webpage, 'swf player URL')
        _uuid = uuid.uuid4().hex

        enc_key = self.get_enc_key(swf_url, video_id)

        raw_data = self.get_raw_data(tvid, video_id, enc_key, _uuid)

        if raw_data['code'] != 'A000000':
            raise ExtractorError('Unable to load data. Error code: ' + raw_data['code'])

        if not raw_data['data']['vp']['tkl']:
            raise ExtractorError('No support iQiqy VIP video')

        data = raw_data['data']

        return {
            'id': video_id,
            'title': data['vi']['vn'],
            'formats': self.construct_formats(data, video_id, _uuid),
        }
