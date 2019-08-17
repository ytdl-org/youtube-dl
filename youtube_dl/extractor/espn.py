from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .once import OnceIE
from ..utils import (
    determine_ext,
    int_or_none,
    unified_timestamp,
)


class ESPNIE(OnceIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:
                                (?:
                                    (?:(?:\w+\.)+)?espn\.go|
                                    (?:www\.)?espn
                                )\.com/
                                (?:
                                    (?:
                                        video/(?:clip|iframe/twitter)|
                                        watch/player
                                    )
                                    (?:
                                        .*?\?.*?\bid=|
                                        /_/id/
                                    )|
                                    [^/]+/video/
                                )
                            )|
                            (?:www\.)espnfc\.(?:com|us)/(?:video/)?[^/]+/\d+/video/
                        )
                        (?P<id>\d+)
                    '''

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
        'url': 'http://nonredline.sports.espn.go.com/video/clip?id=19744672',
        'only_matching': True,
    }, {
        'url': 'https://cdn.espn.go.com/video/clip/_/id/19771774',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/watch/player?id=19141491',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/watch/player?bucketId=257&id=19505875',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/watch/player/_/id/19141491',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/video/clip?id=10365079',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/video/clip/_/id/17989860',
        'only_matching': True,
    }, {
        'url': 'https://espn.go.com/video/iframe/twitter/?cms=espn&id=10365079',
        'only_matching': True,
    }, {
        'url': 'http://www.espnfc.us/video/espn-fc-tv/86/video/3319154/nashville-unveiled-as-the-newest-club-in-mls',
        'only_matching': True,
    }, {
        'url': 'http://www.espnfc.com/english-premier-league/23/video/3324163/premier-league-in-90-seconds-golden-tweets',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/espnw/video/26066627/arkansas-gibson-completes-hr-cycle-four-innings',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        data_id = self._search_regex(r'data-cerebro-id="(.*?)"', webpage, 'data_id', group=1)

        request_url = 'https://watch.auth.api.espn.com/video/auth/getclip/%s?apikey=5p8m6dw513q716wt2os04mec3' % data_id

        clip = self._download_xml(
            request_url,
            video_id).findall('clip')[0]

        title = clip.findall('headline')[0].text

        format_urls = set()
        formats = []

        def traverse_source(source):
            for element in source.iter():
                if element.tag == 'transcodes':
                    continue
                extract_source(element.text, element.tag)

        def extract_source(source_url, source_id=None):
            if source_url in format_urls:
                return
            format_urls.add(source_url)
            ext = determine_ext(source_url)
            if OnceIE.suitable(source_url):
                formats.extend(self._extract_once_formats(source_url))
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    source_url, video_id, fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=source_id, fatal=False))
            else:
                f = {
                    'url': source_url,
                    'format_id': source_id,
                }
                mobj = re.search(r'(\d+)p(\d+)_(\d+)k\.', source_url)
                if mobj:
                    f.update({
                        'height': int(mobj.group(1)),
                        'fps': int(mobj.group(2)),
                        'tbr': int(mobj.group(3)),
                    })
                if source_id == 'mezzanine':
                    f['preference'] = 1
                formats.append(f)

        links = clip.findall('transcodes')[0]
        traverse_source(links)
        self._sort_formats(formats)

        description = clip.findall('caption')[0].text
        duration = int_or_none(clip.findall('durationSeconds')[0].text)
        timestamp = unified_timestamp(clip.findall('publishDate')[0].text)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }


class ESPNArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:espn\.go|(?:www\.)?espn)\.com/(?:[^/]+/)*(?P<id>[^/]+)'
    _TESTS = [{
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


class FiveThirtyEightIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fivethirtyeight\.com/features/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://fivethirtyeight.com/features/how-the-6-8-raiders-can-still-make-the-playoffs/',
        'info_dict': {
            'id': '56032156',
            'ext': 'flv',
            'title': 'FiveThirtyEight: The Raiders can still make the playoffs',
            'description': 'Neil Paine breaks down the simplest scenario that will put the Raiders into the playoffs at 8-8.',
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        embed_url = self._search_regex(
            r'<iframe[^>]+src=["\'](https?://fivethirtyeight\.abcnews\.go\.com/video/embed/\d+/\d+)',
            webpage, 'embed url')

        return self.url_result(embed_url, 'AbcNewsVideo')
