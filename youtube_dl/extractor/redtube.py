from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_to_int,
    unified_strdate,
)


class RedTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redtube\.com/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.redtube.com/66418',
        'md5': '7b8c22b5e7098a3e1c09709df1126d2d',
        'info_dict': {
            'id': '66418',
            'ext': 'mp4',
            'title': 'Sucked on a toilet',
            'upload_date': '20120831',
            'duration': 596,
            'view_count': int,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if any(s in webpage for s in ['video-deleted-info', '>This video has been removed']):
            raise ExtractorError('Video %s has been removed' % video_id, expected=True)

        title = self._html_search_regex(
            (r'<h1 class="videoTitle[^"]*">(?P<title>.+?)</h1>',
             r'videoTitle\s*:\s*(["\'])(?P<title>)\1'),
            webpage, 'title', group='title')

        formats = []
        sources = self._parse_json(
            self._search_regex(
                r'sources\s*:\s*({.+?})', webpage, 'source', default='{}'),
            video_id, fatal=False)
        if sources and isinstance(sources, dict):
            for format_id, format_url in sources.items():
                if format_url:
                    formats.append({
                        'url': format_url,
                        'format_id': format_id,
                        'height': int_or_none(format_id),
                    })
        else:
            video_url = self._html_search_regex(
                r'<source src="(.+?)" type="video/mp4">', webpage, 'video URL')
            formats.append({'url': video_url})
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage)
        upload_date = unified_strdate(self._search_regex(
            r'<span[^>]+class="added-time"[^>]*>ADDED ([^<]+)<',
            webpage, 'upload date', fatal=False))
        duration = int_or_none(self._search_regex(
            r'videoDuration\s*:\s*(\d+)', webpage, 'duration', fatal=False))
        view_count = str_to_int(self._search_regex(
            r'<span[^>]*>VIEWS</span></td>\s*<td>([\d,.]+)',
            webpage, 'view count', fatal=False))

        # No self-labeling, but they describe themselves as
        # "Home of Videos Porno"
        age_limit = 18

        return {
            'id': video_id,
            'ext': 'mp4',
            'title': title,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'age_limit': age_limit,
            'formats': formats,
        }
