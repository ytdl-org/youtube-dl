from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    extract_attributes,
    int_or_none,
    parse_age_limit,
    ExtractorError,
)


class DiscoveryGoIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?(?:
            discovery|
            investigationdiscovery|
            discoverylife|
            animalplanet|
            ahctv|
            destinationamerica|
            sciencechannel|
            tlc|
            velocitychannel
        )go\.com/(?:[^/]+/)*(?P<id>[^/?#&]+)'''
    _TEST = {
        'url': 'https://www.discoverygo.com/love-at-first-kiss/kiss-first-ask-questions-later/',
        'info_dict': {
            'id': '57a33c536b66d1cd0345eeb1',
            'ext': 'mp4',
            'title': 'Kiss First, Ask Questions Later!',
            'description': 'md5:fe923ba34050eae468bffae10831cb22',
            'duration': 2579,
            'series': 'Love at First Kiss',
            'season_number': 1,
            'episode_number': 1,
            'age_limit': 14,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        container = extract_attributes(
            self._search_regex(
                r'(<div[^>]+class=["\']video-player-container[^>]+>)',
                webpage, 'video container'))

        video = self._parse_json(
            container.get('data-video') or container.get('data-json'),
            display_id)

        title = video['name']

        stream = video.get('stream')
        if not stream:
            if video.get('authenticated') is True:
                raise ExtractorError(
                    'This video is only available via cable service provider subscription that'
                    ' is not currently supported. You may want to use --cookies.', expected=True)
            else:
                raise ExtractorError('Unable to find stream')
        STREAM_URL_SUFFIX = 'streamUrl'
        formats = []
        for stream_kind in ('', 'hds'):
            suffix = STREAM_URL_SUFFIX.capitalize() if stream_kind else STREAM_URL_SUFFIX
            stream_url = stream.get('%s%s' % (stream_kind, suffix))
            if not stream_url:
                continue
            if stream_kind == '':
                formats.extend(self._extract_m3u8_formats(
                    stream_url, display_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif stream_kind == 'hds':
                formats.extend(self._extract_f4m_formats(
                    stream_url, display_id, f4m_id=stream_kind, fatal=False))
        self._sort_formats(formats)

        video_id = video.get('id') or display_id
        description = video.get('description', {}).get('detailed')
        duration = int_or_none(video.get('duration'))

        series = video.get('show', {}).get('name')
        season_number = int_or_none(video.get('season', {}).get('number'))
        episode_number = int_or_none(video.get('episodeNumber'))

        tags = video.get('tags')
        age_limit = parse_age_limit(video.get('parental', {}).get('rating'))

        subtitles = {}
        captions = stream.get('captions')
        if isinstance(captions, list):
            for caption in captions:
                subtitle_url = caption.get('fileUrl')
                if (not subtitle_url or not isinstance(subtitle_url, compat_str) or
                        not subtitle_url.startswith('http')):
                    continue
                lang = caption.get('fileLang', 'en')
                subtitles.setdefault(lang, []).append({'url': subtitle_url})

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'duration': duration,
            'series': series,
            'season_number': season_number,
            'episode_number': episode_number,
            'tags': tags,
            'age_limit': age_limit,
            'formats': formats,
            'subtitles': subtitles,
        }
