# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class XMinusIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?x-minus\.org/track/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://x-minus.org/track/4542/%D0%BF%D0%B5%D1%81%D0%B5%D0%BD%D0%BA%D0%B0-%D1%88%D0%BE%D1%84%D0%B5%D1%80%D0%B0.html',
        'md5': '401a15f2d2dcf6d592cb95528d72a2a8',
        'info_dict': {
            'id': '4542',
            'ext': 'mp3',
            'title': 'Леонид Агутин-Песенка шофера',
            'duration': 156,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # TODO more code goes here, for example ...
        webpage = self._download_webpage(url, video_id)
        artist = self._html_search_regex(
            r'minus_track.artist="(.+?)"', webpage, 'artist')
        title = artist + '-' + self._html_search_regex(
            r'minus_track.title="(.+?)"', webpage, 'title')
        duration = int_or_none(self._html_search_regex(
            r'minus_track.dur_sec=\'([0-9]+?)\'', webpage, 'duration'))
        enc_token = self._html_search_regex(
            r'data-mt="(.*?)"', webpage, 'enc_token')
        token = self._decode_token(enc_token)
        url = 'http://x-minus.org/dwlf/{}/{}.mp3'.format(video_id, token)

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'duration': duration,
        }

    def _decode_token(self, enc_token):
        token = ''
        pos = 0
        for c in reversed(enc_token):
            if pos != 3:
                token += chr(ord(c) - 1)
            else:
                token += c
            pos += 1
        return token
