# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    parse_iso8601,
    unescapeHTML,
)


class RteIE(InfoExtractor):
    IE_NAME = 'rte'
    IE_DESC = 'Raidió Teilifís Éireann TV'
    _VALID_URL = r'https?://(?:www\.)?rte\.ie/player/[^/]{2,3}/show/[^/]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.rte.ie/player/ie/show/iwitness-862/10478715/',
        'info_dict': {
            'id': '10478715',
            'ext': 'flv',
            'title': 'Watch iWitness  online',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'iWitness : The spirit of Ireland, one voice and one minute at a time.',
            'duration': 60.046,
        },
        'params': {
            'skip_download': 'f4m fails with --test atm'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._html_search_meta('description', webpage, 'description')
        duration = float_or_none(self._html_search_meta(
            'duration', webpage, 'duration', fatal=False), 1000)

        thumbnail = None
        thumbnail_meta = self._html_search_meta('thumbnail', webpage)
        if thumbnail_meta:
            thumbnail_id = self._search_regex(
                r'uri:irus:(.+)', thumbnail_meta,
                'thumbnail id', fatal=False)
            if thumbnail_id:
                thumbnail = 'http://img.rasset.ie/%s.jpg' % thumbnail_id

        feeds_url = self._html_search_meta('feeds-prefix', webpage, 'feeds url') + video_id
        json_string = self._download_json(feeds_url, video_id)

        # f4m_url = server + relative_url
        f4m_url = json_string['shows'][0]['media:group'][0]['rte:server'] + json_string['shows'][0]['media:group'][0]['url']
        f4m_formats = self._extract_f4m_formats(f4m_url, video_id)
        self._sort_formats(f4m_formats)

        return {
            'id': video_id,
            'title': title,
            'formats': f4m_formats,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
        }


class RteRadioIE(InfoExtractor):
    IE_NAME = 'rte:radio'
    IE_DESC = 'Raidió Teilifís Éireann radio'
    # Radioplayer URLs have two distinct specifier formats,
    # the old format #!rii=<channel_id>:<id>:<playable_item_id>:<date>:
    # the new format #!rii=b<channel_id>_<id>_<playable_item_id>_<date>_
    # where the IDs are int/empty, the date is DD-MM-YYYY, and the specifier may be truncated.
    # An <id> uniquely defines an individual recording, and is the only part we require.
    _VALID_URL = r'https?://(?:www\.)?rte\.ie/radio/utils/radioplayer/rteradioweb\.html#!rii=(?:b?[0-9]*)(?:%3A|:|%5F|_)(?P<id>[0-9]+)'

    _TESTS = [{
        # Old-style player URL; HLS and RTMPE formats
        'url': 'http://www.rte.ie/radio/utils/radioplayer/rteradioweb.html#!rii=16:10507902:2414:27-12-2015:',
        'info_dict': {
            'id': '10507902',
            'ext': 'mp4',
            'title': 'Gloria',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'md5:9ce124a7fb41559ec68f06387cabddf0',
            'timestamp': 1451203200,
            'upload_date': '20151227',
            'duration': 7230.0,
        },
        'params': {
            'skip_download': 'f4m fails with --test atm'
        }
    }, {
        # New-style player URL; RTMPE formats only
        'url': 'http://rte.ie/radio/utils/radioplayer/rteradioweb.html#!rii=b16_3250678_8861_06-04-2012_',
        'info_dict': {
            'id': '3250678',
            'ext': 'flv',
            'title': 'The Lyric Concert with Paul Herriott',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': '',
            'timestamp': 1333742400,
            'upload_date': '20120406',
            'duration': 7199.016,
        },
        'params': {
            'skip_download': 'f4m fails with --test atm'
        }
    }]

    def _real_extract(self, url):
        item_id = self._match_id(url)

        json_string = self._download_json(
            'http://www.rte.ie/rteavgen/getplaylist/?type=web&format=json&id=' + item_id,
            item_id)

        # NB the string values in the JSON are stored using XML escaping(!)
        show = json_string['shows'][0]
        title = unescapeHTML(show['title'])
        description = unescapeHTML(show.get('description'))
        thumbnail = show.get('thumbnail')
        duration = float_or_none(show.get('duration'), 1000)
        timestamp = parse_iso8601(show.get('published'))

        mg = show['media:group'][0]

        formats = []

        if mg.get('url'):
            m = re.match(r'(?P<url>rtmpe?://[^/]+)/(?P<app>.+)/(?P<playpath>mp4:.*)', mg['url'])
            if m:
                m = m.groupdict()
                formats.append({
                    'url': m['url'] + '/' + m['app'],
                    'app': m['app'],
                    'play_path': m['playpath'],
                    'player_url': url,
                    'ext': 'flv',
                    'format_id': 'rtmp',
                })

        if mg.get('hls_server') and mg.get('hls_url'):
            formats.extend(self._extract_m3u8_formats(
                mg['hls_server'] + mg['hls_url'], item_id, 'mp4',
                entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))

        if mg.get('hds_server') and mg.get('hds_url'):
            formats.extend(self._extract_f4m_formats(
                mg['hds_server'] + mg['hds_url'], item_id,
                f4m_id='hds', fatal=False))

        self._sort_formats(formats)

        return {
            'id': item_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }
