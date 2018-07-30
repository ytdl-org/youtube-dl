# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    parse_age_limit,
    parse_iso8601,
)


class Go90IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?go90\.com/(?:videos|embed)/(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'https://www.go90.com/videos/84BUqjLpf9D',
        'md5': 'efa7670dbbbf21a7b07b360652b24a32',
        'info_dict': {
            'id': '84BUqjLpf9D',
            'ext': 'mp4',
            'title': 'Daily VICE - Inside The Utah Coalition Against Pornography Convention',
            'description': 'VICE\'s Karley Sciortino meets with activists who discuss the state\'s strong anti-porn stance. Then, VICE Sports explains NFL contracts.',
            'timestamp': 1491868800,
            'upload_date': '20170411',
            'age_limit': 14,
        }
    }, {
        'url': 'https://www.go90.com/embed/261MflWkD3N',
        'only_matching': True,
    }]
    _GEO_BYPASS = False

    def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            headers = self.geo_verification_headers()
            headers.update({
                'Content-Type': 'application/json; charset=utf-8',
            })
            video_data = self._download_json(
                'https://www.go90.com/api/view/items/' + video_id, video_id,
                headers=headers, data=b'{"client":"web","device_type":"pc"}')
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                message = self._parse_json(e.cause.read().decode(), None)['error']['message']
                if 'region unavailable' in message:
                    self.raise_geo_restricted(countries=['US'])
                raise ExtractorError(message, expected=True)
            raise

        if video_data.get('requires_drm'):
            raise ExtractorError('This video is DRM protected.', expected=True)
        main_video_asset = video_data['main_video_asset']

        episode_number = int_or_none(video_data.get('episode_number'))
        series = None
        season = None
        season_id = None
        season_number = None
        for metadata in video_data.get('__children', {}).get('Item', {}).values():
            if metadata.get('type') == 'show':
                series = metadata.get('title')
            elif metadata.get('type') == 'season':
                season = metadata.get('title')
                season_id = metadata.get('id')
                season_number = int_or_none(metadata.get('season_number'))

        title = episode = video_data.get('title') or series
        if series and series != title:
            title = '%s - %s' % (series, title)

        thumbnails = []
        formats = []
        subtitles = {}
        for asset in video_data.get('assets'):
            if asset.get('id') == main_video_asset:
                for source in asset.get('sources', []):
                    source_location = source.get('location')
                    if not source_location:
                        continue
                    source_type = source.get('type')
                    if source_type == 'hls':
                        m3u8_formats = self._extract_m3u8_formats(
                            source_location, video_id, 'mp4',
                            'm3u8_native', m3u8_id='hls', fatal=False)
                        for f in m3u8_formats:
                            mobj = re.search(r'/hls-(\d+)-(\d+)K', f['url'])
                            if mobj:
                                height, tbr = mobj.groups()
                                height = int_or_none(height)
                                f.update({
                                    'height': f.get('height') or height,
                                    'width': f.get('width') or int_or_none(height / 9.0 * 16.0 if height else None),
                                    'tbr': f.get('tbr') or int_or_none(tbr),
                                })
                        formats.extend(m3u8_formats)
                    elif source_type == 'dash':
                        formats.extend(self._extract_mpd_formats(
                            source_location, video_id, mpd_id='dash', fatal=False))
                    else:
                        formats.append({
                            'format_id': source.get('name'),
                            'url': source_location,
                            'width': int_or_none(source.get('width')),
                            'height': int_or_none(source.get('height')),
                            'tbr': int_or_none(source.get('bitrate')),
                        })

                for caption in asset.get('caption_metadata', []):
                    caption_url = caption.get('source_url')
                    if not caption_url:
                        continue
                    subtitles.setdefault(caption.get('language', 'en'), []).append({
                        'url': caption_url,
                        'ext': determine_ext(caption_url, 'vtt'),
                    })
            elif asset.get('type') == 'image':
                asset_location = asset.get('location')
                if not asset_location:
                    continue
                thumbnails.append({
                    'url': asset_location,
                    'width': int_or_none(asset.get('width')),
                    'height': int_or_none(asset.get('height')),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': video_data.get('short_description'),
            'like_count': int_or_none(video_data.get('like_count')),
            'timestamp': parse_iso8601(video_data.get('released_at')),
            'series': series,
            'episode': episode,
            'season': season,
            'season_id': season_id,
            'season_number': season_number,
            'episode_number': episode_number,
            'subtitles': subtitles,
            'age_limit': parse_age_limit(video_data.get('rating')),
        }
