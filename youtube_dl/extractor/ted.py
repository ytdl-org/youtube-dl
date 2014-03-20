from __future__ import unicode_literals

import json
import re

from .subtitles import SubtitlesInfoExtractor

from ..utils import (
    compat_str,
)


class TEDIE(SubtitlesInfoExtractor):
    _VALID_URL = r'''(?x)
        (?P<proto>https?://)
        (?P<type>www|embed)(?P<urlmain>\.ted\.com/
        (
            (?P<type_playlist>playlists(?:/\d+)?) # We have a playlist
            |
            ((?P<type_talk>talks)) # We have a simple talk
        )
        (/lang/(.*?))? # The url may contain the language
        /(?P<name>\w+) # Here goes the name and then ".html"
        .*)$
        '''
    _TEST = {
        'url': 'http://www.ted.com/talks/dan_dennett_on_our_consciousness.html',
        'md5': '4ea1dada91e4174b53dac2bb8ace429d',
        'info_dict': {
            'id': '102',
            'ext': 'mp4',
            'title': 'The illusion of consciousness',
            'description': ('Philosopher Dan Dennett makes a compelling '
                'argument that not only don\'t we understand our own '
                'consciousness, but that half the time our brains are '
                'actively fooling us.'),
            'uploader': 'Dan Dennett',
        }
    }

    _FORMATS_PREFERENCE = {
        'low': 1,
        'medium': 2,
        'high': 3,
    }

    def _extract_info(self, webpage):
        info_json = self._search_regex(r'q\("\w+.init",({.+})\)</script>',
            webpage, 'info json')
        return json.loads(info_json)

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url, re.VERBOSE)
        if m.group('type') == 'embed':
            desktop_url = m.group('proto') + 'www' + m.group('urlmain')
            return self.url_result(desktop_url, 'TED')
        name = m.group('name')
        if m.group('type_talk'):
            return self._talk_info(url, name)
        else:
            return self._playlist_videos_info(url, name)

    def _playlist_videos_info(self, url, name):
        '''Returns the videos of the playlist'''

        webpage = self._download_webpage(url, name,
            'Downloading playlist webpage')
        info = self._extract_info(webpage)
        playlist_info = info['playlist']

        playlist_entries = [
            self.url_result(u'http://www.ted.com/talks/' + talk['slug'], self.ie_key())
            for talk in info['talks']
        ]
        return self.playlist_result(
            playlist_entries,
            playlist_id=compat_str(playlist_info['id']),
            playlist_title=playlist_info['title'])

    def _talk_info(self, url, video_name):
        webpage = self._download_webpage(url, video_name)
        self.report_extraction(video_name)

        talk_info = self._extract_info(webpage)['talks'][0]

        formats = [{
            'ext': 'mp4',
            'url': format_url,
            'format_id': format_id,
            'format': format_id,
            'preference': self._FORMATS_PREFERENCE.get(format_id, -1),
        } for (format_id, format_url) in talk_info['nativeDownloads'].items()]
        self._sort_formats(formats)

        video_id = compat_str(talk_info['id'])
        # subtitles
        video_subtitles = self.extract_subtitles(video_id, talk_info)
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, talk_info)
            return

        thumbnail = talk_info['thumb']
        if not thumbnail.startswith('http'):
            thumbnail = 'http://' + thumbnail
        return {
            'id': video_id,
            'title': talk_info['title'],
            'uploader': talk_info['speaker'],
            'thumbnail': thumbnail,
            'description': self._og_search_description(webpage),
            'subtitles': video_subtitles,
            'formats': formats,
        }

    def _get_available_subtitles(self, video_id, talk_info):
        languages = [lang['languageCode'] for lang in talk_info.get('languages', [])]
        if languages:
            sub_lang_list = {}
            for l in languages:
                url = 'http://www.ted.com/talks/subtitles/id/%s/lang/%s/format/srt' % (video_id, l)
                sub_lang_list[l] = url
            return sub_lang_list
        else:
            self._downloader.report_warning(u'video doesn\'t have subtitles')
            return {}
