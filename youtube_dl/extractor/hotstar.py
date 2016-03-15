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

    _GET_CONTENT_TEMPLATE = 'http://account.hotstar.com/AVS/besc?action=GetAggregatedContentDetails&channel=PCTV&contentId=%s'
    _GET_CDN_TEMPLATE = 'http://getcdn.hotstar.com/AVS/besc?action=GetCDN&asJson=Y&channel=%s&id=%s&type=%s'

    def _download_json(self, url_or_request, video_id, note='Downloading JSON metadata', fatal=True):
        json_data = super(HotStarIE, self)._download_json(url_or_request, video_id, note, fatal=fatal)
        if json_data['resultCode'] != 'OK':
            if fatal:
                raise ExtractorError(json_data['errorDescription'])
            return None
        return json_data['resultObj']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            self._GET_CONTENT_TEMPLATE % video_id,
            video_id)['contentInfo'][0]

        formats = []
        # PCTV for extracting f4m manifest
        for f in ('TABLET',):
            format_data = self._download_json(
                self._GET_CDN_TEMPLATE % (f, video_id, 'VOD'),
                video_id, 'Downloading %s JSON metadata' % f, fatal=False)
            if format_data:
                format_url = format_data['src']
                ext = determine_ext(format_url)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(format_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
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
            'title': video_data['episodeTitle'],
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'timestamp': int_or_none(video_data.get('broadcastDate')),
            'formats': formats,
        }
