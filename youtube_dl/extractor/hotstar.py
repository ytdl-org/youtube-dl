# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
)


class HotStarBaseIE(InfoExtractor):
    _GEO_COUNTRIES = ['IN']

    def _download_json(self, *args, **kwargs):
        response = super(HotStarBaseIE, self)._download_json(*args, **kwargs)
        if response['resultCode'] != 'OK':
            if kwargs.get('fatal'):
                raise ExtractorError(
                    response['errorDescription'], expected=True)
            return None
        return response['resultObj']

    def _download_content_info(self, content_id):
        return self._download_json(
            'https://account.hotstar.com/AVS/besc', content_id, query={
                'action': 'GetAggregatedContentDetails',
                'appVersion': '5.0.40',
                'channel': 'PCTV',
                'contentId': content_id,
            })['contentInfo'][0]


class HotStarIE(HotStarBaseIE):
    _VALID_URL = r'https?://(?:www\.)?hotstar\.com/(?:.+?[/-])?(?P<id>\d{10})'
    _TESTS = [{
        'url': 'http://www.hotstar.com/on-air-with-aib--english-1000076273',
        'info_dict': {
            'id': '1000076273',
            'ext': 'mp4',
            'title': 'On Air With AIB',
            'description': 'md5:c957d8868e9bc793ccb813691cc4c434',
            'timestamp': 1447227000,
            'upload_date': '20151111',
            'duration': 381,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://www.hotstar.com/sports/cricket/rajitha-sizzles-on-debut-with-329/2001477583',
        'only_matching': True,
    }, {
        'url': 'http://www.hotstar.com/1000000515',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data = self._download_content_info(video_id)

        title = video_data['episodeTitle']

        if video_data.get('encrypted') == 'Y':
            raise ExtractorError('This video is DRM protected.', expected=True)

        formats = []
        for f in ('JIO',):
            format_data = self._download_json(
                'http://getcdn.hotstar.com/AVS/besc',
                video_id, 'Downloading %s JSON metadata' % f,
                fatal=False, query={
                    'action': 'GetCDN',
                    'asJson': 'Y',
                    'channel': f,
                    'id': video_id,
                    'type': 'VOD',
                })
            if format_data:
                format_url = format_data.get('src')
                if not format_url:
                    continue
                ext = determine_ext(format_url)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        m3u8_id='hls', fatal=False))
                elif ext == 'f4m':
                    # produce broken files
                    continue
                else:
                    formats.append({
                        'url': format_url,
                        'width': int_or_none(format_data.get('width')),
                        'height': int_or_none(format_data.get('height')),
                    })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'timestamp': int_or_none(video_data.get('broadcastDate')),
            'formats': formats,
            'episode': title,
            'episode_number': int_or_none(video_data.get('episodeNumber')),
            'series': video_data.get('contentTitle'),
        }


class HotStarPlaylistIE(HotStarBaseIE):
    IE_NAME = 'hotstar:playlist'
    _VALID_URL = r'(?P<url>https?://(?:www\.)?hotstar\.com/tv/[^/]+/(?P<content_id>\d+))/(?P<type>[^/]+)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.hotstar.com/tv/pratidaan/14982/episodes/14812/9993',
        'info_dict': {
            'id': '14812',
        },
        'playlist_mincount': 75,
    }, {
        'url': 'http://www.hotstar.com/tv/pratidaan/14982/popular-clips/9998/9998',
        'only_matching': True,
    }]
    _ITEM_TYPES = {
        'episodes': 'EPISODE',
        'popular-clips': 'CLIPS',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        base_url = mobj.group('url')
        content_id = mobj.group('content_id')
        playlist_type = mobj.group('type')

        content_info = self._download_content_info(content_id)
        playlist_id = compat_str(content_info['categoryId'])

        collection = self._download_json(
            'https://search.hotstar.com/AVS/besc', playlist_id, query={
                'action': 'SearchContents',
                'appVersion': '5.0.40',
                'channel': 'PCTV',
                'moreFilters': 'series:%s;' % playlist_id,
                'query': '*',
                'searchOrder': 'last_broadcast_date desc,year desc,title asc',
                'type': self._ITEM_TYPES.get(playlist_type, 'EPISODE'),
            })

        entries = [
            self.url_result(
                '%s/_/%s' % (base_url, video['contentId']),
                ie=HotStarIE.ie_key(), video_id=video['contentId'])
            for video in collection['response']['docs']
            if video.get('contentId')]

        return self.playlist_result(entries, playlist_id)
