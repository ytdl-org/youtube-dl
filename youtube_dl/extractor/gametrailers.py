from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_age_limit,
    url_basename,
)


class GametrailersIE(InfoExtractor):
    _VALID_URL = r'https?://www\.gametrailers\.com/videos/view/[^/]+/(?P<id>.+)'

    _TEST = {
        'url': 'http://www.gametrailers.com/videos/view/gametrailers-com/116437-Just-Cause-3-Review',
        'md5': 'f28c4efa0bdfaf9b760f6507955b6a6a',
        'info_dict': {
            'id': '2983958',
            'ext': 'mp4',
            'display_id': '116437-Just-Cause-3-Review',
            'title': 'Just Cause 3 - Review',
            'description': 'It\'s a lot of fun to shoot at things and then watch them explode in Just Cause 3, but should there be more to the experience than that?',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        title = self._html_search_regex(
            r'<title>(.+?)\|', webpage, 'title').strip()
        embed_url = self._proto_relative_url(
            self._search_regex(
                r'src=\'(//embed.gametrailers.com/embed/[^\']+)\'', webpage,
                'embed url'),
            scheme='http:')
        video_id = url_basename(embed_url)
        embed_page = self._download_webpage(embed_url, video_id)
        embed_vars_json = self._search_regex(
            r'(?s)var embedVars = (\{.*?\})\s*</script>', embed_page,
            'embed vars')
        info = self._parse_json(embed_vars_json, video_id)

        formats = []
        for media in info['media']:
            if media['mediaPurpose'] == 'play':
                formats.append({
                    'url': media['uri'],
                    'height': media['height'],
                    'width:': media['width'],
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': info.get('thumbUri'),
            'description': self._og_search_description(webpage),
            'duration': int_or_none(info.get('videoLengthInSeconds')),
            'age_limit': parse_age_limit(info.get('audienceRating')),
        }
