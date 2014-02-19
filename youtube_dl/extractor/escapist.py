from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,

    ExtractorError,
)


class EscapistIE(InfoExtractor):
    _VALID_URL = r'^https?://?(www\.)?escapistmagazine\.com/videos/view/(?P<showname>[^/]+)/(?P<id>[0-9]+)-'
    _TEST = {
        'url': 'http://www.escapistmagazine.com/videos/view/the-escapist-presents/6618-Breaking-Down-Baldurs-Gate',
        'md5': 'ab3a706c681efca53f0a35f1415cf0d1',
        'info_dict': {
            'id': '6618',
            'ext': 'mp4',
            'description': "Baldur's Gate: Original, Modded or Enhanced Edition? I'll break down what you can expect from the new Baldur's Gate: Enhanced Edition.",
            'uploader': 'the-escapist-presents',
            'title': "Breaking Down Baldur's Gate",
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        showName = mobj.group('showname')
        video_id = mobj.group('id')

        self.report_extraction(video_id)
        webpage = self._download_webpage(url, video_id)

        videoDesc = self._html_search_regex(
            r'<meta name="description" content="([^"]*)"',
            webpage, 'description', fatal=False)

        playerUrl = self._og_search_video_url(webpage, name=u'player URL')

        title = self._html_search_regex(
            r'<meta name="title" content="([^"]*)"',
            webpage, 'title').split(' : ')[-1]

        configUrl = self._search_regex('config=(.*)$', playerUrl, 'config URL')
        configUrl = compat_urllib_parse.unquote(configUrl)

        formats = []

        def _add_format(name, cfgurl, quality):
            config = self._download_json(
                cfgurl, video_id,
                'Downloading ' + name + ' configuration',
                'Unable to download ' + name + ' configuration',
                transform_source=lambda s: s.replace("'", '"'))

            playlist = config['playlist']
            formats.append({
                'url': playlist[1]['url'],
                'format_id': name,
                'quality': quality,
            })

        _add_format('normal', configUrl, quality=0)
        hq_url = (configUrl +
                  ('&hq=1' if '?' in configUrl else configUrl + '?hq=1'))
        try:
            _add_format('hq', hq_url, quality=1)
        except ExtractorError:
            pass  # That's fine, we'll just use normal quality

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'uploader': showName,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': videoDesc,
            'player_url': playerUrl,
        }
