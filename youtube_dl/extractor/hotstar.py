# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
)


class HotStarIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hotstar\.com/(?:.+?[/-])?(?P<id>\d{10})'
    _TESTS = [{
        'url': 'http://www.hotstar.com/on-air-with-aib--english-1000076273',
        'info_dict': {
            'id': '1000076273',
            'ext': 'mp4',
            'title': 'On Air With AIB - English',
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

    def _download_json(self, url_or_request, video_id, note='Downloading JSON metadata', fatal=True, query=None):
        json_data = super(HotStarIE, self)._download_json(
            url_or_request, video_id, note, fatal=fatal, query=query)
        if json_data['resultCode'] != 'OK':
            if fatal:
                raise ExtractorError(json_data['errorDescription'])
            return None
        return json_data['resultObj']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'http://account.hotstar.com/AVS/besc', video_id, query={
                'action': 'GetAggregatedContentDetails',
                'channel': 'PCTV',
                'contentId': video_id,
            })['contentInfo'][0]
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
