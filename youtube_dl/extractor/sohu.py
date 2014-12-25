# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .common import compat_str


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

            return self._download_json(
                base_data_url + vid_id, video_id,
                'Downloading JSON data for %s' % vid_id)

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        mytv = mobj.group('mytv') is not None

        webpage = self._download_webpage(url, video_id)
        raw_title = self._html_search_regex(
            r'(?s)<title>(.+?)</title>',
            webpage, 'video title')
        title = raw_title.partition('-')[0].strip()

        vid = self._html_search_regex(
            r'var vid ?= ?["\'](\d+)["\']',
            webpage, 'video path')
        vid_data = _fetch_data(vid, mytv)

        formats_json = {}
        for format_id in ('nor', 'high', 'super', 'ori', 'h2644k', 'h2654k'):
            vid_id = vid_data['data'].get('%sVid' % format_id)
            if not vid_id:
                continue
            vid_id = compat_str(vid_id)
            formats_json[format_id] = vid_data if vid == vid_id else _fetch_data(vid_id, mytv)

        part_count = vid_data['data']['totalBlocks']

        playlist = []
        for i in range(part_count):
            formats = []
            for format_id, format_data in formats_json.items():
                allot = format_data['allot']
                prot = format_data['prot']

                data = format_data['data']
                clips_url = data['clipsURL']
                su = data['su']

                part_str = self._download_webpage(
                    'http://%s/?prot=%s&file=%s&new=%s' %
                    (allot, prot, clips_url[i], su[i]),
                    video_id,
                    'Downloading %s video URL part %d of %d'
                    % (format_id, i + 1, part_count))

                part_info = part_str.split('|')
                video_url = '%s%s?key=%s' % (part_info[0], su[i], part_info[3])

                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'filesize': data['clipsBytes'][i],
                    'width': data['width'],
                    'height': data['height'],
                    'fps': data['fps'],
                })
            self._sort_formats(formats)

            playlist.append({
                'id': '%s_part%d' % (video_id, i + 1),
                'title': title,
                'duration': vid_data['data']['clipsDuration'][i],
                'formats': formats,
            })

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
