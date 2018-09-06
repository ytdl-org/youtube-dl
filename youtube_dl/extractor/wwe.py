from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import urljoin


class WWEIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?wwe.com/(?:.*/)?videos/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.wwe.com/videos/daniel-bryan-vs-andrade-cien-almas-smackdown-live-sept-4-2018',
        'md5': '30cbc824b51f4010ea885bfcaec76972',
        'info_dict': {
            'id': '40048199',
            'ext': 'mp4',
            'title': 'Daniel Bryan vs. Andrade "Cien" Almas: SmackDown LIVE, Sept. 4, 2018',
            'description': 'Still fuming after he and his wife Brie Bella were attacked by The Miz and Maryse last week, Daniel Bryan takes care of some unfinished business with Andrade "Cien" Almas.',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'https://de.wwe.com/videos/gran-metalik-vs-tony-nese-wwe-205-live-sept-4-2018',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        drupal_settings = self._parse_json(
            self._html_search_regex(
                r'(?s)Drupal\.settings\s*,\s*({.+?})\);',
                webpage, 'drupal settings'),
            display_id)

        player = drupal_settings['WWEVideoLanding']['initialVideo']
        metadata = player['playlist'][0]

        id = compat_str(metadata['nid'])
        title = metadata.get('title') or self._og_search_title(webpage)
        video_url = 'https:' + metadata['file']
        thumbnail = None
        if metadata.get('image') is not None:
            thumbnail = urljoin(url, metadata.get('image'))
        description = metadata.get('description')

        formats = self._extract_m3u8_formats(video_url, id, 'mp4')

        return {
            'id': id,
            'title': title,
            'formats': formats,
            'url': video_url,
            'display_id': display_id,
            'thumbnail': thumbnail,
            'description': description,
        }
