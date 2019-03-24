# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    try_get,
    unified_timestamp,
)


class TuneInBaseIE(InfoExtractor):
    _METADATA_API_BASE_URL = 'https://api.tunein.com/profiles/%s%s/contents?partnerId=RadioTime&version=3.1002'
    _STREAM_API_BASE_URL = 'https://opml.radiotime.com/Tune.ashx?id=%s%s&render=json&formats=mp3,aac,ogg,flash,html,hls'

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src=["\'](?P<url>(?:https?://)?tunein\.com/embed/player/[pst]\d+)',
            webpage)

    def _real_extract(self, url):
        content_id = self._match_id(url)

        metadata = self._download_json(
            self._METADATA_API_BASE_URL % (self._CONTENT_TYPE, content_id),
            content_id, note='Downloading JSON metadata')

        station_info = metadata['Items'][0]['Children'][0]
        title = compat_str(station_info['Title'])

        play_info = try_get(station_info, lambda x: x['Actions']['Play']) or {}
        stream_url = play_info.get('PlayUrl')

        formats = []
        if not stream_url:
            streams = self._download_json(
                self._STREAM_API_BASE_URL % (self._CONTENT_TYPE, content_id),
                content_id, note='Downloading stream data')['body']

            streams = list(
                filter(lambda s: s.get('media_type') != 'html', streams))
            if not streams:
                raise ExtractorError(
                    'No downloadable streams found', expected=True)

            for stream in streams:
                media_type = try_get(stream, lambda x: x['media_type'], compat_str)
                reliability = int_or_none(stream.get('reliability'))
                format_note = (
                    'Reliability: %d%%' % reliability
                    if reliability is not None else None)
                formats.append({
                    'abr': int_or_none(stream.get('bitrate')),
                    'ext': media_type.lower() if media_type else None,
                    'acodec': media_type,
                    'vcodec': 'none',
                    'url': stream.get('url'),
                    'source_preference': reliability,
                    'format_note': format_note,
                })

            self._sort_formats(formats)

        s = station_info
        is_live = play_info.get('IsLive') is True
        res = {
            'id': content_id,
            'title': self._live_title(title) if is_live else title,
            'description': s.get('Description') or s.get('Subtitle'),
            'thumbnail': s.get('Image'),
            'is_live': is_live,
            'duration': int_or_none(play_info.get('Duration')),
            'timestamp': unified_timestamp(play_info.get('PublishTime'))
        }

        if stream_url:
            res['url'] = stream_url
        else:
            res['formats'] = formats

        return res


class TuneInStationIE(TuneInBaseIE):
    IE_NAME = 'tunein:station'
    _VALID_URL = r'https?://(?:www\.)?tunein\.com/(?:radio/.*?-s|station/.*?StationId=|embed/player/s)(?P<id>\d+)'
    _CONTENT_TYPE = 's'  # station

    _TESTS = [{
        'url': 'http://tunein.com/radio/Jazz24-885-s34682/',
        'info_dict': {
            'id': '34682',
            'title': 're:Jazz24',
            'description': 'md5:c94dad268809130da5c91b0760f366a1',
            'ext': 'mp3'
        },
        'params': {
            'skip_download': True,  # live stream
        },
    }, {
        'url': 'http://tunein.com/embed/player/s6404/',
        'only_matching': True,
    }]


class TuneInProgramIE(TuneInBaseIE):
    IE_NAME = 'tunein:program'
    _VALID_URL = r'https?://(?:www\.)?tunein\.com/(?:(?:radio|podcasts)/.*?-p|program/.*?ProgramId=|embed/player/p)(?P<id>\d+)'
    _CONTENT_TYPE = 'p'  # program

    _TESTS = [{
        'url': 'https://tunein.com/podcasts/Business--Economics-Podcasts/Planet-Money-p164680/',
        'info_dict': {
            'id': '164680'
        },
        'playlist_mincount': 190
    }, {
        'url': 'https://tunein.com/radio/Planet-Money-p164680/',
        'only_matching': True,
    }, {
        'url': 'http://tunein.com/embed/player/p191660/',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if TuneInTopicIE.suitable(url) else super(TuneInProgramIE, cls).suitable(url)

    def _process_page(self, page):
        if not page.get('Items'):
            raise ExtractorError(
                'No downloadable episodes found', expected=True)

        for item in page.get('Items'):
            video_id = compat_str(item['GuideId'][1:])
            url = 'http://tunein.com/topic/?TopicId=%s' % video_id
            title = item.get('Title')
            yield self.url_result(url, TuneInTopicIE.ie_key(), video_id, title)

    def _entries(self, program_id):
        offset = 0
        limit = 100
        has_more = True
        while has_more:
            page = self._download_json(
                self._METADATA_API_BASE_URL % (self._CONTENT_TYPE, program_id),
                program_id,
                note='Downloading program data from offset %s' % offset,
                query={'filter': 't:free', 'offset': offset, 'limit': limit})

            for entry in self._process_page(page):
                yield entry

            has_more = try_get(
                page,
                lambda p: p['Paging']['Next'], compat_str) is not None

            if has_more:
                offset += page['Paging']['ItemCount']

    def _real_extract(self, url):
        program_id = self._match_id(url)
        return self.playlist_result(self._entries(program_id), program_id)


class TuneInTopicIE(TuneInBaseIE):
    IE_NAME = 'tunein:topic'
    _VALID_URL = r'https?://(?:www\.)?tunein\.com/(?:(?:topic|podcasts)/.*?(?:T|t)opicId=|embed/player/t)(?P<id>\d+)'
    _CONTENT_TYPE = 't'  # topic

    _TESTS = [{
        'url': 'https://tunein.com/podcasts/Business--Economics-Podcasts/Planet-Money-p164680/?topicId=129983955',
        'info_dict': {
            'id': '129983955',
            'title': '#901: Bad Cops Are Expensive',
            'ext': 'mp3',
            'description': 'md5:0e702acc52914c55219b1b06a6026a87',
            'upload_date': '20190322',
            'timestamp': 1553292060,
        },
    }, {
        'url': 'http://tunein.com/topic/?TopicId=129983955',
        'only_matching': True,
    }, {
        'url': 'http://tunein.com/embed/player/t129983955/',
        'only_matching': True,
    }]


class TuneInShortenerIE(InfoExtractor):
    IE_NAME = 'tunein:shortener'
    IE_DESC = False  # Do not list
    _VALID_URL = r'https?://tun\.in/(?P<id>[A-Za-z0-9]+)'

    _TEST = {
        # test redirection
        'url': 'http://tun.in/ser7s',
        'info_dict': {
            'id': '34682',
            'title': 're:Jazz24',
            'description': 'md5:c94dad268809130da5c91b0760f366a1',
            'ext': 'mp3'
        },
        'params': {
            'skip_download': True,  # live stream
        },
    }

    def _real_extract(self, url):
        redirect_id = self._match_id(url)
        # The server doesn't support HEAD requests
        urlh = self._request_webpage(
            url, redirect_id, note='Downloading redirect page')
        url = urlh.geturl()
        self.to_screen('Following redirect: %s' % url)
        return self.url_result(url)
