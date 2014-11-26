# encoding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class SohuIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<mytv>my\.)?tv\.sohu\.com/.+?/(?(mytv)|n)(?P<id>\d+)\.shtml.*?'

    _TEST = {
        'url': 'http://tv.sohu.com/20130724/n382479172.shtml#super',
        'md5': 'bde8d9a6ffd82c63a1eefaef4eeefec7',
        'info_dict': {
            'id': '382479172',
            'ext': 'mp4',
            'title': 'MV：Far East Movement《The Illest》',
        },
        'skip': 'Only available from China',
    }

    def _real_extract(self, url):

        def _fetch_data(vid_id, mytv=False):
            if mytv:
                base_data_url = 'http://my.tv.sohu.com/play/videonew.do?vid='
            else:
                base_data_url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid='
            data_url = base_data_url + str(vid_id)
            data_json = self._download_webpage(
                data_url, video_id,
                note='Downloading JSON data for ' + str(vid_id))
            return json.loads(data_json)

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        mytv = mobj.group('mytv') is not None

        webpage = self._download_webpage(url, video_id)
        raw_title = self._html_search_regex(r'(?s)<title>(.+?)</title>',
                                            webpage, 'video title')
        title = raw_title.partition('-')[0].strip()

        vid = self._html_search_regex(r'var vid ?= ?["\'](\d+)["\']', webpage,
                                      'video path')
        data = _fetch_data(vid, mytv)

        QUALITIES = ('ori', 'super', 'high', 'nor')
        vid_ids = [data['data'][q + 'Vid']
                   for q in QUALITIES
                   if data['data'][q + 'Vid'] != 0]
        if not vid_ids:
            raise ExtractorError('No formats available for this video')

        # For now, we just pick the highest available quality
        vid_id = vid_ids[-1]

        format_data = data if vid == vid_id else _fetch_data(vid_id, mytv)
        part_count = format_data['data']['totalBlocks']
        allot = format_data['allot']
        prot = format_data['prot']
        clipsURL = format_data['data']['clipsURL']
        su = format_data['data']['su']

        playlist = []
        for i in range(part_count):
            part_url = ('http://%s/?prot=%s&file=%s&new=%s' %
                        (allot, prot, clipsURL[i], su[i]))
            part_str = self._download_webpage(
                part_url, video_id,
                note='Downloading part %d of %d' % (i + 1, part_count))

            part_info = part_str.split('|')
            video_url = '%s%s?key=%s' % (part_info[0], su[i], part_info[3])

            video_info = {
                'id': '%s_part%02d' % (video_id, i + 1),
                'title': title,
                'url': video_url,
                'ext': 'mp4',
            }
            playlist.append(video_info)

        if len(playlist) == 1:
            info = playlist[0]
            info['id'] = video_id
        else:
            info = {
                '_type': 'playlist',
                'entries': playlist,
                'id': video_id,
            }

        return info
