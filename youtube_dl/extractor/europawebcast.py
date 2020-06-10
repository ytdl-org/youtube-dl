# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class EuropaWebcastIE(InfoExtractor):
    _VALID_URL = r'https?://webcast.ec.europa.eu/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://webcast.ec.europa.eu/copyright-stakeholder-dialogues',
        'md5': 'cb2873afec20f44a6521eb99b90864ec',
        'info_dict': {
            'id': 'copyright-stakeholder-dialogues',
            'ext': 'mp4',
            'title': 'COPYRIGHT STAKEHOLDER DIALOGUES',
            'timestamp': 1571126116,
            'upload_date': '20191015',
            'duration': 21600,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        session_data = self._parse_json(
            self._search_regex(r'var\s+sessionData\s*=\s*({.+});', webpage,
                               'session data', fatal=False), video_id)
        media_setup = self._parse_json(
            self._search_regex(r'var\s+mediaSetup\s*=\s*({.+});', webpage,
                               'media setup'), video_id)
        playlist_item = media_setup['playlist'][0]

        title = session_data.get('name') or self._html_search_regex(
            r'<span[^>]+class="[^"]*(?:pageSectionTitle|sessionTitle)[^>]+>([^<]+)</span>',
            webpage, 'title')
        start_time = playlist_item.get('startUTC')
        stop_time = playlist_item.get('stopUTC')

        if start_time and stop_time:
            duration = stop_time - start_time
        else:
            duration = None

        source_data = playlist_item['source']
        base_url = 'https://%s/%s/' % (
            media_setup['server'], media_setup['application'])
        formats = []

        for lang in source_data['languages']:
            lang_formats = []

            for quality in source_data['qualities']:
                lang_formats.extend(self._extract_m3u8_formats(
                    '%s%s/playlist.m3u8?tracks=%s' % (
                        base_url, source_data['qualities'][quality], lang), video_id,
                    ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id='%s-%s' % (quality, lang)))

            if lang == 'or':
                for fmt in lang_formats:
                    fmt['preference'] = 1  # prefer original language
            else:
                for fmt in lang_formats:
                    fmt['language'] = lang

            formats.extend(lang_formats)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'timestamp': start_time,
            'duration': duration,
        }
