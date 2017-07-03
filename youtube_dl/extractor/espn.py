from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    int_or_none,
    unified_timestamp,
)


class ESPNIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:(\w+\.)+)?espn\.go|(?:www\.)?espn)\.com/(?:video/clip(?:\?.*?\bid=|/_/id/)|watch/player\?.*?\bid=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://espn.go.com/video/clip?id=10365079',
        'info_dict': {
            'id': '10365079',
            'ext': 'mp4',
            'title': '30 for 30 Shorts: Judging Jewell',
            'description': 'md5:39370c2e016cb4ecf498ffe75bef7f0f',
            'timestamp': 1390936111,
            'upload_date': '20140128',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://broadband.espn.go.com/video/clip?id=18910086',
        'info_dict': {
            'id': '18910086',
            'ext': 'mp4',
            'title': 'Kyrie spins around defender for two',
            'description': 'md5:2b0f5bae9616d26fba8808350f0d2b9b',
            'timestamp': 1489539155,
            'upload_date': '20170315',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Unable to download f4m manifest'],
    }, {
        'url': 'http://nonredline.sports.espn.go.com/video/clip?id=19744672',
        'info_dict': {
            'id': '19744672',
            'ext': 'mp4',
            'title': 'Aggies use 2016 season as motivation',
            'description': 'md5:2fe30038633f86408a184ec676c5fdac',
            'timestamp': 1498519201,
            'upload_date': '20170626',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Unable to download f4m manifest'],
    }, {
        'url': 'https://cdn.espn.go.com/video/clip/_/id/19771774',
        'info_dict': {
            'id': '19771774',
            'ext': 'mp4',
            'title': 'Coach Cal to the Knicks? Not so fast',
            'description': 'md5:a60393eaee9c203dd4184c48c308651b',
            'timestamp': 1498806684,
            'upload_date': '20170630',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Unable to download f4m manifest'],
    }, {
        'url': 'http://www.espn.com/watch/player?id=19141491',
        'info_dict': {
            'id': '19141491',
            'ext': 'mp4',
            'title': 'Stephen A.: Lynch was wrong for slapping phone out of fan\'s hand',
            'description': 'md5:9b31cf7b31e85c6dfcdefd11571e6c8e',
            'timestamp': 1492011670,
            'upload_date': '20170412',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Unable to download f4m manifest'],
    }, {
        'url': 'http://www.espn.com/watch/player?bucketId=257&id=19505875',
        'info_dict': {
            'id': '19505875',
            'ext': 'mp4',
            'title': 'Six-year-old Fuller nails first word at Spelling Bee',
            'description': 'md5:f90babb45b196d7c8ca1d295bb68e36a',
            'timestamp': 1496252167,
            'upload_date': '20170531',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Unable to download f4m manifest'],
    }, {
        'url': 'http://www.espn.com/video/clip?id=10365079',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/video/clip/_/id/17989860',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        clip = self._download_json(
            'http://api-app.espn.com/v1/video/clips/%s' % video_id,
            video_id)['videos'][0]

        title = clip['headline']

        format_urls = set()
        formats = []

        def traverse_source(source, base_source_id=None):
            for source_id, source in source.items():
                if isinstance(source, compat_str):
                    extract_source(source, base_source_id)
                elif isinstance(source, dict):
                    traverse_source(
                        source,
                        '%s-%s' % (base_source_id, source_id)
                        if base_source_id else source_id)

        def extract_source(source_url, source_id=None):
            if source_url in format_urls:
                return
            format_urls.add(source_url)
            ext = determine_ext(source_url)
            if ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    source_url, video_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    source_url, video_id, f4m_id=source_id, fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=source_id, fatal=False))
            else:
                formats.append({
                    'url': source_url,
                    'format_id': source_id,
                })

        traverse_source(clip['links']['source'])
        self._sort_formats(formats)

        description = clip.get('caption') or clip.get('description')
        thumbnail = clip.get('thumbnail')
        duration = int_or_none(clip.get('duration'))
        timestamp = unified_timestamp(clip.get('originalPublishDate'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }


class ESPNArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:espn\.go|(?:www\.)?espn)\.com/(?:[^/]+/)*(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://espn.go.com/video/iframe/twitter/?cms=espn&id=10365079',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/nba/recap?gameId=400793786',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/blog/golden-state-warriors/post/_/id/593/how-warriors-rapidly-regained-a-winning-edge',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/sports/endurance/story/_/id/12893522/dzhokhar-tsarnaev-sentenced-role-boston-marathon-bombings',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/nba/playoffs/2015/story/_/id/12887571/john-wall-washington-wizards-no-swelling-left-hand-wrist-game-5-return',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if ESPNIE.suitable(url) else super(ESPNArticleIE, cls).suitable(url)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'class=(["\']).*?video-play-button.*?\1[^>]+data-id=["\'](?P<id>\d+)',
            webpage, 'video id', group='id')

        return self.url_result(
            'http://espn.go.com/video/clip?id=%s' % video_id, ESPNIE.ie_key())
