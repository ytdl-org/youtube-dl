from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import compat_urllib_request

from ..utils import (
    determine_ext,
    clean_html,
    qualities,
)


def _decrypt_config(key, string):
    a = ''
    i = ''
    r = ''

    while len(a) < (len(string) / 2):
        a += key

    a = a[0:int(len(string) / 2)]

    t = 0
    while t < len(string):
        i += chr(int(string[t] + string[t + 1], 16))
        t += 2

    icko = [s for s in i]

    for t, c in enumerate(a):
        r += chr(ord(c) ^ ord(icko[t]))

    return r


class EscapistIE(InfoExtractor):
    _VALID_URL = r'https?://?(www\.)?escapistmagazine\.com/videos/view/[^/?#]+/(?P<id>[0-9]+)-[^/?#]*(?:$|[?#])'
    _TESTS = [{
        'url': 'http://www.escapistmagazine.com/videos/view/the-escapist-presents/6618-Breaking-Down-Baldurs-Gate',
        'md5': 'c6793dbda81388f4264c1ba18684a74d',
        'info_dict': {
            'id': '6618',
            'ext': 'mp4',
            'description': "Baldur's Gate: Original, Modded or Enhanced Edition? I'll break down what you can expect from the new Baldur's Gate: Enhanced Edition.",
            'title': "Breaking Down Baldur's Gate",
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 264,
        }
    }, {
        'url': 'http://www.escapistmagazine.com/videos/view/zero-punctuation/10044-Evolve-One-vs-Multiplayer',
        'md5': 'cf8842a8a46444d241f9a9980d7874f2',
        'info_dict': {
            'id': '10044',
            'ext': 'mp4',
            'description': 'This week, Zero Punctuation reviews Evolve.',
            'title': 'Evolve - One vs Multiplayer',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 304,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        imsVideo = self._parse_json(
            self._search_regex(
                r'imsVideo\.play\(({.+?})\);', webpage, 'imsVideo'),
            video_id)
        video_id = imsVideo['videoID']
        key = imsVideo['hash']

        quality = qualities(['lq', 'hq', 'hd'])

        formats = []
        for q in ['lq', 'hq', 'hd']:
            config_req = compat_urllib_request.Request(
                'http://www.escapistmagazine.com/videos/'
                'vidconfig.php?videoID=%s&hash=%s&quality=%s' % (video_id, key, 'mp4_' + q))
            config_req.add_header('Referer', url)
            config = self._download_webpage(config_req, video_id, 'Downloading video config ' + q.upper())

            data = json.loads(_decrypt_config(key, config))

            title = clean_html(data['videoData']['title'])
            duration = data['videoData']['duration'] / 1000

            for i, v in enumerate(data['files']['videos']):

                formats.append({
                    'url': v,
                    'format_id': determine_ext(v) + '_' + q + str(i),
                    'quality': quality(q),
                })

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'duration': duration,
        }
