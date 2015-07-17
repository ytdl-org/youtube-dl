import re

from .common import InfoExtractor
from ..utils import RegexNotFoundError

class GoogleDriveEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:video\.google\.com/get_player\?.*?docid=|(?:docs|drive)\.google\.com/file/d/)(?P<id>[a-zA-Z0-9_-]{28})'
    _TEST = {
        'url': 'https://docs.google.com/file/d/0B8KB9DRosYGKMXNoeWxqa3JYclE/preview',
        'info_dict': {
            'id': '0B8KB9DRosYGKMXNoeWxqa3JYclE',
            'ext': 'mp4',
            'title': 'Jimmy Fallon Sings Since You\'ve Been Gone.wmv',
        }
    }

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe src="https?://(?:video\.google\.com/get_player\?.*?docid=|(?:docs|drive)\.google\.com/file/d/)(?P<id>[a-zA-Z0-9_-]{28})',
            webpage)
        if mobj:
            return 'https://drive.google.com/file/d/%s' % mobj.group('id')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return {
            '_type': 'url',
            'ie_key': 'GoogleDrive',
            'url': 'https://drive.google.com/file/d/%s' % video_id
        }

class GoogleDriveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:docs|drive)\.google\.com/(?:uc\?.*?id=|file/d/)(?P<id>[a-zA-Z0-9_-]{28})'
    _TEST = {
        'url': 'https://drive.google.com/file/d/0ByeS4oOUV-49Zzh4R1J6R09zazQ/edit?pli=1',
        'info_dict': {
            'id': '0ByeS4oOUV-49Zzh4R1J6R09zazQ',
            'ext': 'mp4',
            'title': 'Big Buck Bunny.mp4',
        }
    }
    _formats = {
        '5': {'ext': 'flv'},
        '6': {'ext': 'flv'},
        '13': {'ext': '3gp'},
        '17': {'ext': '3gp'},
        '18': {'ext': 'mp4'},
        '22': {'ext': 'mp4'},
        '34': {'ext': 'flv'},
        '35': {'ext': 'flv'},
        '36': {'ext': '3gp'},
        '37': {'ext': 'mp4'},
        '38': {'ext': 'mp4'},
        '43': {'ext': 'webm'},
        '44': {'ext': 'webm'},
        '45': {'ext': 'webm'},
        '46': {'ext': 'webm'},
        '59': {'ext': 'mp4'}
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://docs.google.com/file/d/' + video_id, video_id, encoding='unicode_escape'
        )
        try:
            title = self._html_search_regex(
                r'"title"\s*,\s*"([^"]+)',
                webpage,
                'title'
            )
            fmt_stream_map = self._html_search_regex(
                r'"fmt_stream_map"\s*,\s*"([^"]+)',
                webpage,
                'fmt_stream_map'
            )
            fmt_list = self._html_search_regex(
                r'"fmt_list"\s*,\s*"([^"]+)',
                webpage,
                'fmt_list'
            )
#			timestamp = self._html_search_regex(
#				r'"timestamp"\s*,\s*"([^"]+)',
#				webpage,
#				'timestamp'
#			)
            length_seconds = self._html_search_regex(
                r'"length_seconds"\s*,\s*"([^"]+)',
                webpage,
                'length_seconds'
            )
        except RegexNotFoundError:
            try:
                reason = self._html_search_regex(
                    r'"reason","([^"]+)',
                    webpage,
                    'reason'
                )
                self.report_warning(reason)
                return
            except RegexNotFoundError:
                self.report_warning('not a video')
                return

        fmt_stream_map = fmt_stream_map.split(',')
        fmt_list = fmt_list.split(',')
        formats = []
        for i in range(len(fmt_stream_map)):
            fmt_id, fmt_url = fmt_stream_map[i].split('|')
            resolution = fmt_list[i].split('/')[1]
            width, height = resolution.split('x')
            formats.append({
                'url': fmt_url,
                'format_id': fmt_id,
                'resolution': resolution,
                'width': int(width),
                'height': int(height),
                'ext': self._formats[fmt_id]['ext']
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
#           'timestamp': int(timestamp),
            'duration': int(length_seconds),
            'formats': formats
        }
