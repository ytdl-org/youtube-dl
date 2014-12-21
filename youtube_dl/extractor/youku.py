# coding: utf-8

from __future__ import unicode_literals

import math
import random
import re
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class YoukuIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        (?:
            http://(?:v|player)\.youku\.com/(?:v_show/id_|player\.php/sid/)|
            youku:)
        (?P<id>[A-Za-z0-9]+)(?:\.html|/v\.swf|)
    '''
    _TEST = {
        'url': 'http://v.youku.com/v_show/id_XNDgyMDQ2NTQw.html',
        'md5': 'ffe3f2e435663dc2d1eea34faeff5b5b',
        'params': {
            'test': False
        },
        'info_dict': {
            'id': 'XNDgyMDQ2NTQw_part00',
            'ext': 'flv',
            'title': 'youtube-dl test video "\'/\\ä↭𝕐'
        }
    }

    def _gen_sid(self):
        nowTime = int(time.time() * 1000)
        random1 = random.randint(1000, 1998)
        random2 = random.randint(1000, 9999)

        return "%d%d%d" % (nowTime, random1, random2)

    def _get_file_ID_mix_string(self, seed):
        mixed = []
        source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\:._-1234567890")
        seed = float(seed)
        for i in range(len(source)):
            seed = (seed * 211 + 30031) % 65536
            index = math.floor(seed / 65536 * len(source))
            mixed.append(source[int(index)])
            source.remove(source[int(index)])
        # return ''.join(mixed)
        return mixed

    def _get_file_id(self, fileId, seed):
        mixed = self._get_file_ID_mix_string(seed)
        ids = fileId.split('*')
        realId = []
        for ch in ids:
            if ch:
                realId.append(mixed[int(ch)])
        return ''.join(realId)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        info_url = 'http://v.youku.com/player/getPlayList/VideoIDS/' + video_id

        config = self._download_json(info_url, video_id)

        error_code = config['data'][0].get('error_code')
        if error_code:
            # -8 means blocked outside China.
            error = config['data'][0].get('error')  # Chinese and English, separated by newline.
            raise ExtractorError(error or 'Server reported error %i' % error_code,
                                 expected=True)

        video_title = config['data'][0]['title']
        seed = config['data'][0]['seed']

        format = self._downloader.params.get('format', None)
        supported_format = list(config['data'][0]['streamfileids'].keys())

        # TODO proper format selection
        if format is None or format == 'best':
            if 'hd2' in supported_format:
                format = 'hd2'
            else:
                format = 'flv'
            ext = 'flv'
        elif format == 'worst':
            format = 'mp4'
            ext = 'mp4'
        else:
            format = 'flv'
            ext = 'flv'

        fileid = config['data'][0]['streamfileids'][format]
        keys = [s['k'] for s in config['data'][0]['segs'][format]]
        # segs is usually a dictionary, but an empty *list* if an error occured.

        files_info = []
        sid = self._gen_sid()
        fileid = self._get_file_id(fileid, seed)

        # column 8,9 of fileid represent the segment number
        # fileid[7:9] should be changed
        for index, key in enumerate(keys):
            temp_fileid = '%s%02X%s' % (fileid[0:8], index, fileid[10:])
            download_url = 'http://k.youku.com/player/getFlvPath/sid/%s_%02X/st/flv/fileid/%s?k=%s' % (sid, index, temp_fileid, key)

            info = {
                'id': '%s_part%02d' % (video_id, index),
                'url': download_url,
                'uploader': None,
                'upload_date': None,
                'title': video_title,
                'ext': ext,
            }
            files_info.append(info)

        return files_info
