from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    parse_filesize,
    unified_strdate,
)


class FreesoundIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?freesound\.org/people/([^/]+)/sounds/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.freesound.org/people/miklovan/sounds/194503/',
        'md5': '12280ceb42c81f19a515c745eae07650',
        'info_dict': {
            'id': '194503',
            'ext': 'mp3',
            'title': 'gulls in the city.wav',
            'uploader': 'miklovan',
            'description': 'the sounds of seagulls in the city',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        music_id = mobj.group('id')
        webpage = self._download_webpage(url, music_id)

        audio_url = self._og_search_property('audio', webpage, 'song url')
        title = self._og_search_property('audio:title', webpage, 'song title')
        duration = float_or_none(get_element_by_class('duration', webpage), scale=1000)
        tags = get_element_by_class('tags', webpage)
        sound_info = get_element_by_id('sound_information_box', webpage)
        release_date = get_element_by_id('sound_date', webpage)

        description = self._html_search_regex(
            r'<div id="sound_description">(.*?)</div>', webpage, 'description',
            fatal=False, flags=re.DOTALL)

        download_count = int_or_none(self._html_search_regex(
            r'Downloaded.*>(\d+)<', webpage, 'downloaded', fatal=False))

        filesize = float_or_none(parse_filesize(self._search_regex(
            r'Filesize</dt><dd>(.*)</dd>', sound_info, 'file size (approx)', fatal=False)))

        if release_date:
            release_date = unified_strdate(release_date.replace('th', ''))

        bitdepth = self._html_search_regex(
            r'Bitdepth</dt><dd>(.*)</dd>', sound_info, 'Bitdepth', fatal=False)

        channels = self._html_search_regex(
            r'Channels</dt><dd>(.*)</dd>', sound_info, 'Channels info', fatal=False)

        formats = [{
            'url': audio_url,
            'id': music_id,
            'format_id': self._og_search_property('audio:type', webpage, 'audio format', fatal=False),
            'format_note': '{0} {1} {2}'.format(determine_ext(audio_url), bitdepth, channels),
            'filesize_approx': filesize,
            'asr': int_or_none(self._html_search_regex(
                r'Samplerate</dt><dd>(\d+).*</dd>',
                sound_info, 'samplerate', fatal=False)),
        }]

        return {
            'id': music_id,
            'title': title,
            'uploader': self._og_search_property('audio:artist', webpage, 'music uploader', fatal=False),
            'description': description,
            'duration': duration,
            'tags': [self._html_search_regex(r'>(.*)</a>', t, 'tag', fatal=False)
                     for t in tags.split('\n') if t.strip()],
            'formats': formats,
            'release_date': release_date,
            'likes_count': download_count,
        }
