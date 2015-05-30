# encoding: utf-8
from __future__ import unicode_literals

import re

from .crunchyroll import CrunchyrollIE

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    ExtractorError,
    int_or_none,
    remove_start,
    xpath_text,
)


class SoompiBaseIE(InfoExtractor):
    def _get_episodes(self, webpage, episode_filter=None):
        episodes = self._parse_json(
            self._search_regex(
                r'VIDEOS\s*=\s*(\[.+?\]);', webpage, 'episodes JSON'),
            None)
        return list(filter(episode_filter, episodes))


class SoompiIE(SoompiBaseIE, CrunchyrollIE):
    IE_NAME = 'soompi'
    _VALID_URL = r'https?://tv\.soompi\.com/(?:en/)?watch/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://tv.soompi.com/en/watch/29235',
        'info_dict': {
            'id': '29235',
            'ext': 'mp4',
            'title': 'Episode 1096',
            'description': '2015-05-20'
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _get_episode(self, webpage, video_id):
        return self._get_episodes(webpage, lambda x: x['id'] == video_id)[0]

    def _get_subtitles(self, config, video_id):
        sub_langs = {}
        for subtitle in config.findall('./{default}preload/subtitles/subtitle'):
            sub_langs[subtitle.attrib['id']] = subtitle.attrib['title']

        subtitles = {}
        for s in config.findall('./{default}preload/subtitle'):
            lang_code = sub_langs.get(s.attrib['id'])
            if not lang_code:
                continue
            sub_id = s.get('id')
            data = xpath_text(s, './data', 'data')
            iv = xpath_text(s, './iv', 'iv')
            if not id or not iv or not data:
                continue
            subtitle = self._decrypt_subtitles(data, iv, sub_id).decode('utf-8')
            subtitles[lang_code] = self._extract_subtitles(subtitle)
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            webpage = self._download_webpage(
                url, video_id, 'Downloading episode page')
        except ExtractorError as ee:
            if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 403:
                webpage = ee.cause.read()
                block_message = self._html_search_regex(
                    r'(?s)<div class="block-message">(.+?)</div>', webpage,
                    'block message', default=None)
                if block_message:
                    raise ExtractorError(block_message, expected=True)
            raise

        formats = []
        config = None
        for format_id in re.findall(r'\?quality=([0-9a-zA-Z]+)', webpage):
            config = self._download_xml(
                'http://tv.soompi.com/en/show/_/%s-config.xml?mode=hls&quality=%s' % (video_id, format_id),
                video_id, 'Downloading %s XML' % format_id)
            m3u8_url = xpath_text(
                config, './{default}preload/stream_info/file',
                '%s m3u8 URL' % format_id)
            if not m3u8_url:
                continue
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id=format_id))
        self._sort_formats(formats)

        episode = self._get_episode(webpage, video_id)

        title = episode['name']
        description = episode.get('description')
        duration = int_or_none(episode.get('duration'))

        thumbnails = [{
            'id': thumbnail_id,
            'url': thumbnail_url,
        } for thumbnail_id, thumbnail_url in episode.get('img_url', {}).items()]

        subtitles = self.extract_subtitles(config, video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles
        }


class SoompiShowIE(SoompiBaseIE):
    IE_NAME = 'soompi:show'
    _VALID_URL = r'https?://tv\.soompi\.com/en/shows/(?P<id>[0-9a-zA-Z\-_]+)'
    _TESTS = [{
        'url': 'http://tv.soompi.com/en/shows/liar-game',
        'info_dict': {
            'id': 'liar-game',
            'title': 'Liar Game',
            'description': 'md5:52c02bce0c1a622a95823591d0589b66',
        },
        'playlist_count': 14,
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)

        webpage = self._download_webpage(
            url, show_id, 'Downloading show page')

        title = remove_start(self._og_search_title(webpage), 'SoompiTV | ')
        description = self._og_search_description(webpage)

        entries = [
            self.url_result('http://tv.soompi.com/en/watch/%s' % episode['id'], 'Soompi')
            for episode in self._get_episodes(webpage)]

        return self.playlist_result(entries, show_id, title, description)
