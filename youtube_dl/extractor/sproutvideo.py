# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..compat import (
    compat_b64decode,
    compat_urllib_parse_urlencode,
)


class SproutVideoIE(InfoExtractor):
    _VALID_URL = r'(?:https?:|)//videos.sproutvideo.com/embed/(?P<id>[a-f0-9]+)/[a-f0-9]+\??.*'
    _TEST = {
        'url': 'https://videos.sproutvideo.com/embed/4c9dddb01910e3c9c4/0fc24387c4f24ee3',
        'md5': '1343ce1a6cb39d67889bfa07c7b02b0e',
        'info_dict': {
            'id': '4c9dddb01910e3c9c4',
            'ext': 'mp4',
            'title': 'Adrien Labaeye : Berlin, des communautés aux communs',
        }
    }

    @staticmethod
    def _extract_url(webpage):
        sproutvideo = re.search(
            r'(?:<iframe\s+class=[\'\"]sproutvideo-player.*src|href)=[\'\"](?P<url>%s)[\'\"]' % SproutVideoIE._VALID_URL, webpage)
        if sproutvideo:
            return sproutvideo.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        data = self._search_regex(r'<script[^>]+>var dat = \'([^\']+)\';</script>', webpage, 'data')
        data_decoded = compat_b64decode(data).decode('utf-8')
        parsed_data = self._parse_json(data_decoded, video_id)

        # https://github.com/ytdl-org/youtube-dl/issues/16996#issuecomment-406901324
        # signature->m for manifests
        # signature->k for keys
        # signature->t for segments
        m_sig = self._policy_to_qs(parsed_data, 'm')
        k_sig = self._policy_to_qs(parsed_data, 'k')
        t_sig = self._policy_to_qs(parsed_data, 't')

        url = "https://{0}.videos.sproutvideo.com/{1}/{2}/video/index.m3u8?{3}"
        url = url.format(parsed_data['base'],
                         parsed_data['s3_user_hash'],
                         parsed_data['s3_video_hash'],
                         m_sig)

        formats = self._extract_m3u8_formats(url, video_id, 'mp4', 'm3u8_native',
                                             m3u8_id='hls', fatal=False)
        self._sort_formats(formats)

        for i in range(len(formats)):
            formats[i]['url'] = "{}?{}".format(formats[i]['url'], m_sig)

        return {
            'id': video_id,
            'title': parsed_data['title'],
            'formats': formats,
            'force_hlsdl': True,  # currently FFmpeg is not supported
            'extra_param_to_segment_url': t_sig,
            'extra_param_to_key_url': k_sig
        }

    def _format_qsdata(self, qs_data):
        parsed_dict = dict()
        for key in qs_data:
            parsed_dict[key.replace('CloudFront-', '')] = qs_data[key]
        return parsed_dict

    def _policy_to_qs(self, policy, key):
        sig = self._format_qsdata(policy['signatures'][key])
        sig['sessionID'] = policy['sessionID']
        return compat_urllib_parse_urlencode(sig, doseq=True)
