# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .subtitles import SubtitlesInfoExtractor
from ..compat import (
    compat_urllib_request,
    compat_urllib_parse,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
)


class CeskaTelevizeIE(SubtitlesInfoExtractor):
    _VALID_URL = r'https?://www\.ceskatelevize\.cz/(porady|ivysilani)/(.+/)?(?P<id>[^?#]+)'

    _TESTS = [
        {
            'url': 'http://www.ceskatelevize.cz/ivysilani/ivysilani/10441294653-hyde-park-civilizace/214411058091220',
            'info_dict': {
                'id': '214411058091220',
                'ext': 'mp4',
                'title': 'Hyde Park Civilizace',
                'description': 'Věda a současná civilizace. Interaktivní pořad - prostor pro vaše otázky a komentáře',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 3350,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ceskatelevize.cz/ivysilani/10532695142-prvni-republika/bonus/14716-zpevacka-z-duparny-bobina',
            'info_dict': {
                'id': '14716',
                'ext': 'mp4',
                'title': 'První republika: Zpěvačka z Dupárny Bobina',
                'description': 'Sága mapující atmosféru první republiky od r. 1918 do r. 1945.',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 88.4,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        url = url.replace('/porady/', '/ivysilani/').replace('/video/', '')

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        NOT_AVAILABLE_STRING = 'This content is not available at your territory due to limited copyright.'
        if '%s</p>' % NOT_AVAILABLE_STRING in webpage:
            raise ExtractorError(NOT_AVAILABLE_STRING, expected=True)

        typ = self._html_search_regex(r'getPlaylistUrl\(\[\{"type":"(.+?)","id":".+?"\}\],', webpage, 'type')
        episode_id = self._html_search_regex(r'getPlaylistUrl\(\[\{"type":".+?","id":"(.+?)"\}\],', webpage, 'episode_id')

        data = {
            'playlist[0][type]': typ,
            'playlist[0][id]': episode_id,
            'requestUrl': compat_urllib_parse_urlparse(url).path,
            'requestSource': 'iVysilani',
        }

        req = compat_urllib_request.Request(
            'http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist',
            data=compat_urllib_parse.urlencode(data))

        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        req.add_header('x-addr', '127.0.0.1')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        req.add_header('Referer', url)

        playlistpage = self._download_json(req, video_id)

        playlist_url = playlistpage['url']
        if playlist_url == 'error_region':
            raise ExtractorError(NOT_AVAILABLE_STRING, expected=True)

        req = compat_urllib_request.Request(compat_urllib_parse.unquote(playlist_url))
        req.add_header('Referer', url)

        playlist = self._download_json(req, video_id)

        item = playlist['playlist'][0]
        formats = []
        for format_id, stream_url in item['streamUrls'].items():
            formats.extend(self._extract_m3u8_formats(stream_url, video_id, 'mp4'))
        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        duration = float_or_none(item.get('duration'))
        thumbnail = item.get('previewImageUrl')

        subtitles = {}
        subs = item.get('subtitles')
        if subs:
            subtitles['cs'] = subs[0]['url']

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, subtitles)
            return

        subtitles = self._fix_subtitles(self.extract_subtitles(video_id, subtitles))

        return {
            'id': episode_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }

    @staticmethod
    def _fix_subtitles(subtitles):
        """ Convert millisecond-based subtitles to SRT """
        if subtitles is None:
            return subtitles  # subtitles not requested

        def _msectotimecode(msec):
            """ Helper utility to convert milliseconds to timecode """
            components = []
            for divider in [1000, 60, 60, 100]:
                components.append(msec % divider)
                msec //= divider
            return "{3:02}:{2:02}:{1:02},{0:03}".format(*components)

        def _fix_subtitle(subtitle):
            for line in subtitle.splitlines():
                m = re.match(r"^\s*([0-9]+);\s*([0-9]+)\s+([0-9]+)\s*$", line)
                if m:
                    yield m.group(1)
                    start, stop = (_msectotimecode(int(t)) for t in m.groups()[1:])
                    yield "{0} --> {1}".format(start, stop)
                else:
                    yield line

        fixed_subtitles = {}
        for k, v in subtitles.items():
            fixed_subtitles[k] = "\r\n".join(_fix_subtitle(v))
        return fixed_subtitles
