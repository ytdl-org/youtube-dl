from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
)
from ..utils import (
    ExtractorError,
    js_to_json,
)


class EscapistIE(InfoExtractor):
    _VALID_URL = r'https?://?(www\.)?escapistmagazine\.com/videos/view/[^/?#]+/(?P<id>[0-9]+)-[^/?#]*(?:$|[?#])'
    _TEST = {
        'url': 'http://www.escapistmagazine.com/videos/view/the-escapist-presents/6618-Breaking-Down-Baldurs-Gate',
        'md5': 'ab3a706c681efca53f0a35f1415cf0d1',
        'info_dict': {
            'id': '6618',
            'ext': 'mp4',
            'description': "Baldur's Gate: Original, Modded or Enhanced Edition? I'll break down what you can expect from the new Baldur's Gate: Enhanced Edition.",
            'uploader_id': 'the-escapist-presents',
            'uploader': 'The Escapist Presents',
            'title': "Breaking Down Baldur's Gate",
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        uploader_id = self._html_search_regex(
            r"<h1 class='headline'><a href='/videos/view/(.*?)'",
            webpage, 'uploader ID', fatal=False)
        uploader = self._html_search_regex(
            r"<h1 class='headline'>(.*?)</a>",
            webpage, 'uploader', fatal=False)
        description = self._html_search_meta('description', webpage)

        raw_title = self._html_search_meta('title', webpage, fatal=True)
        title = raw_title.partition(' : ')[2]

        player_url = self._og_search_video_url(webpage, name='player URL')
        config_url = compat_urllib_parse.unquote(self._search_regex(
            r'config=(.*)$', player_url, 'config URL'))

        formats = []

        def _add_format(name, cfgurl, quality):
            config = self._download_json(
                cfgurl, video_id,
                'Downloading ' + name + ' configuration',
                'Unable to download ' + name + ' configuration',
                transform_source=js_to_json)

            playlist = config['playlist']
            video_url = next(
                p['url'] for p in playlist
                if p.get('eventCategory') == 'Video')
            formats.append({
                'url': video_url,
                'format_id': name,
                'quality': quality,
            })

        _add_format('normal', config_url, quality=0)
        hq_url = (config_url +
                  ('&hq=1' if '?' in config_url else config_url + '?hq=1'))
        try:
            _add_format('hq', hq_url, quality=1)
        except ExtractorError:
            pass  # That's fine, we'll just use normal quality

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': description,
            'player_url': player_url,
        }
