from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_duration,
    urljoin,
)


class YourPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sxyprn\.com/post/(?P<id>[^/?#&.]+)'
    _TESTS = [{
        'url': 'https://sxyprn.com/post/57ffcb2e1179b.html',
        'md5': '6f8682b6464033d87acaa7a8ff0c092e',
        'info_dict': {
            'id': '57ffcb2e1179b',
            'ext': 'mp4',
            'title': 'md5:c9f43630bd968267672651ba905a7d35',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 165,
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://sxyprn.com/post/5acfc82b12d00.html',
        'md5': '1df93ede16d87685aa069f56ac69b0e7',
        'info_dict': {
            'id': '5acfc82b12d00',
            'ext': 'mp4',
            'title': 'Girls Do Porn E157 The Mormon Girl this should be in HD... #GirlsDoPorn #GDP #BigTits #casting',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2466,
            'age_limit': 18,
        },
    }, {
        'url': 'https://sxyprn.com/post/57ffcb2e1179b.html',
        'only_matching': True,
    }, {
        'url': 'https://sxyprn.com/post/5af15f6799de9.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        get_duration = lambda webpage: parse_duration(self._search_regex(
            r'duration\s*:\s*<[^>]+>([\d:]+)', webpage, 'duration',
            default=None))

        # Only for posts containing a single video is the post_id equal to
        # video_id. If there a multiple videos there also exists a post with the
        # video_id and we use this page to fetch the video title.
        post_id = self._match_id(url)

        webpage = self._download_webpage(url, post_id)

        videos = self._parse_json(
            self._search_regex(
                r'data-vnfo=(["\'])(?P<data>{.+?})\1', webpage, 'data info',
                group='data'),
            post_id)

        for video_id in videos:
            parts = videos[video_id].split('/')
            num = 0
            for c in parts[6] + parts[7]:
                if c.isnumeric():
                    num += int(c)
            parts[5] = compat_str(int(parts[5]) - num)
            parts[1] += '8'
            videos[video_id] = urljoin(url, '/'.join(parts))

        # If there ist only one video in the post (as is most likely) the
        # video_id is equal to post_id and we save us from re-fetching the page
        # to obtain the meta data.
        # This may fail but if needed will be obtained in the next step.
        titles = {
            post_id: self._og_search_description(webpage, default=None)
        }
        thumbnails = {
            post_id: self._og_search_thumbnail(webpage, default=None)
        }
        durations = {
            post_id: get_duration(webpage)
        }

        # obtain missing metadata for all videos in the post
        for video_id in videos:
            if not titles.get(video_id) or not thumbnails.get(video_id) or video_id not in durations:
                webpage = self._download_webpage('https://sxyprn.com/post/%s.html' % video_id, video_id)
            if not titles.get(video_id):
                titles[video_id] = self._og_search_description(webpage)
            if not thumbnails.get(video_id):
                thumbnails[video_id] = self._og_search_thumbnail(webpage)
            if video_id not in durations:
                durations[video_id] = get_duration(webpage)

        entries = []
        for video_id in videos:
            entries.append({
                'id': video_id,
                'url': videos[video_id],
                'title': titles[video_id],
                'thumbnail': thumbnails[video_id],
                'duration': durations[video_id],
                'age_limit': 18,
                'ext': 'mp4',
            })

        if len(entries) == 1:
            return entries[0]
        else:
            return self.playlist_result(entries, post_id, titles[post_id])
