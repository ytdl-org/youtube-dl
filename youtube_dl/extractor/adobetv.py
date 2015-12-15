from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_duration,
    unified_strdate,
    str_to_int,
    int_or_none,
    float_or_none,
    ISO639Utils,
    determine_ext,
)


class AdobeTVBaseIE(InfoExtractor):
    _API_BASE_URL = 'http://tv.adobe.com/api/v4/'


class AdobeTVIE(AdobeTVBaseIE):
    _VALID_URL = r'https?://tv\.adobe\.com/(?:(?P<language>fr|de|es|jp)/)?watch/(?P<show_urlname>[^/]+)/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://tv.adobe.com/watch/the-complete-picture-with-julieanne-kost/quick-tip-how-to-draw-a-circle-around-an-object-in-photoshop/',
        'md5': '9bc5727bcdd55251f35ad311ca74fa1e',
        'info_dict': {
            'id': '10981',
            'ext': 'mp4',
            'title': 'Quick Tip - How to Draw a Circle Around an Object in Photoshop',
            'description': 'md5:99ec318dc909d7ba2a1f2b038f7d2311',
            'thumbnail': 're:https?://.*\.jpg$',
            'upload_date': '20110914',
            'duration': 60,
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        language, show_urlname, urlname = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'

        video_data = self._download_json(
            self._API_BASE_URL + 'episode/get/?language=%s&show_urlname=%s&urlname=%s&disclosure=standard' % (language, show_urlname, urlname),
            urlname)['data'][0]

        formats = [{
            'url': source['url'],
            'format_id': source.get('quality_level') or source['url'].split('-')[-1].split('.')[0] or None,
            'width': int_or_none(source.get('width')),
            'height': int_or_none(source.get('height')),
            'tbr': int_or_none(source.get('video_data_rate')),
        } for source in video_data['videos']]
        self._sort_formats(formats)

        return {
            'id': compat_str(video_data['id']),
            'title': video_data['title'],
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnail'),
            'upload_date': unified_strdate(video_data.get('start_date')),
            'duration': parse_duration(video_data.get('duration')),
            'view_count': str_to_int(video_data.get('playcount')),
            'formats': formats,
        }


class AdobeTVPlaylistBaseIE(AdobeTVBaseIE):
    def _parse_page_data(self, page_data):
        return [self.url_result(self._get_element_url(element_data)) for element_data in page_data]

    def _extract_playlist_entries(self, url, display_id):
        page = self._download_json(url, display_id)
        entries = self._parse_page_data(page['data'])
        for page_num in range(2, page['paging']['pages'] + 1):
            entries.extend(self._parse_page_data(
                self._download_json(url + '&page=%d' % page_num, display_id)['data']))
        return entries


class AdobeTVShowIE(AdobeTVPlaylistBaseIE):
    _VALID_URL = r'https?://tv\.adobe\.com/(?:(?P<language>fr|de|es|jp)/)?show/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://tv.adobe.com/show/the-complete-picture-with-julieanne-kost',
        'info_dict': {
            'id': '36',
            'title': 'The Complete Picture with Julieanne Kost',
            'description': 'md5:fa50867102dcd1aa0ddf2ab039311b27',
        },
        'playlist_mincount': 136,
    }

    def _get_element_url(self, element_data):
        return element_data['urls'][0]

    def _real_extract(self, url):
        language, show_urlname = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'
        query = 'language=%s&show_urlname=%s' % (language, show_urlname)

        show_data = self._download_json(self._API_BASE_URL + 'show/get/?%s' % query, show_urlname)['data'][0]

        return self.playlist_result(
            self._extract_playlist_entries(self._API_BASE_URL + 'episode/?%s' % query, show_urlname),
            compat_str(show_data['id']),
            show_data['show_name'],
            show_data['show_description'])


class AdobeTVChannelIE(AdobeTVPlaylistBaseIE):
    _VALID_URL = r'https?://tv\.adobe\.com/(?:(?P<language>fr|de|es|jp)/)?channel/(?P<id>[^/]+)(?:/(?P<category_urlname>[^/]+))?'

    _TEST = {
        'url': 'http://tv.adobe.com/channel/development',
        'info_dict': {
            'id': 'development',
        },
        'playlist_mincount': 96,
    }

    def _get_element_url(self, element_data):
        return element_data['url']

    def _real_extract(self, url):
        language, channel_urlname, category_urlname = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'
        query = 'language=%s&channel_urlname=%s' % (language, channel_urlname)
        if category_urlname:
            query += '&category_urlname=%s' % category_urlname

        return self.playlist_result(
            self._extract_playlist_entries(self._API_BASE_URL + 'show/?%s' % query, channel_urlname),
            channel_urlname)


class AdobeTVVideoIE(InfoExtractor):
    _VALID_URL = r'https?://video\.tv\.adobe\.com/v/(?P<id>\d+)'

    _TEST = {
        # From https://helpx.adobe.com/acrobat/how-to/new-experience-acrobat-dc.html?set=acrobat--get-started--essential-beginners
        'url': 'https://video.tv.adobe.com/v/2456/',
        'md5': '43662b577c018ad707a63766462b1e87',
        'info_dict': {
            'id': '2456',
            'ext': 'mp4',
            'title': 'New experience with Acrobat DC',
            'description': 'New experience with Acrobat DC',
            'duration': 248.667,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(url + '?format=json', video_id)

        formats = [{
            'format_id': '%s-%s' % (determine_ext(source['src']), source.get('height')),
            'url': source['src'],
            'width': int_or_none(source.get('width')),
            'height': int_or_none(source.get('height')),
            'tbr': int_or_none(source.get('bitrate')),
        } for source in video_data['sources']]
        self._sort_formats(formats)

        # For both metadata and downloaded files the duration varies among
        # formats. I just pick the max one
        duration = max(filter(None, [
            float_or_none(source.get('duration'), scale=1000)
            for source in video_data['sources']]))

        subtitles = {}
        for translation in video_data.get('translations', []):
            lang_id = translation.get('language_w3c') or ISO639Utils.long2short(translation['language_medium'])
            if lang_id not in subtitles:
                subtitles[lang_id] = []
            subtitles[lang_id].append({
                'url': translation['vttPath'],
                'ext': 'vtt',
            })

        return {
            'id': video_id,
            'formats': formats,
            'title': video_data['title'],
            'description': video_data.get('description'),
            'thumbnail': video_data['video'].get('poster'),
            'duration': duration,
            'subtitles': subtitles,
        }
