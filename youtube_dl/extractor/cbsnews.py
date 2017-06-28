# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .cbs import CBSIE
from ..utils import (
    parse_duration,
)


class CBSNewsIE(CBSIE):
    IE_NAME = 'cbsnews'
    IE_DESC = 'CBS News'
    _VALID_URL = r'https?://(?:www\.)?cbsnews\.com/(?:news|videos)/(?P<id>[\da-z_-]+)'

    _TESTS = [
        {
            # 60 minutes
            'url': 'http://www.cbsnews.com/news/artificial-intelligence-positioned-to-be-a-game-changer/',
            'info_dict': {
                'id': '_B6Ga3VJrI4iQNKsir_cdFo9Re_YJHE_',
                'ext': 'mp4',
                'title': 'Artificial Intelligence',
                'description': 'md5:8818145f9974431e0fb58a1b8d69613c',
                'thumbnail': r're:^https?://.*\.jpg$',
                'duration': 1606,
                'uploader': 'CBSI-NEW',
                'timestamp': 1498431900,
                'upload_date': '20170625',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.cbsnews.com/videos/fort-hood-shooting-army-downplays-mental-illness-as-cause-of-attack/',
            'info_dict': {
                'id': 'SNJBOYzXiWBOvaLsdzwH8fmtP1SCd91Y',
                'ext': 'mp4',
                'title': 'Fort Hood shooting: Army downplays mental illness as cause of attack',
                'description': 'md5:4a6983e480542d8b333a947bfc64ddc7',
                'upload_date': '20140404',
                'timestamp': 1396650660,
                'uploader': 'CBSI-NEW',
                'thumbnail': r're:^https?://.*\.jpg$',
                'duration': 205,
                'subtitles': {
                    'en': [{
                        'ext': 'ttml',
                    }],
                },
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            # 48 hours
            'url': 'http://www.cbsnews.com/news/maria-ridulph-murder-will-the-nations-oldest-cold-case-to-go-to-trial-ever-get-solved/',
            'info_dict': {
                'id': 'QpM5BJjBVEAUFi7ydR9LusS69DPLqPJ1',
                'ext': 'mp4',
                'title': 'Cold as Ice',
                'description': 'Can a childhood memory of a friend\'s murder solve a 1957 cold case? "48 Hours" correspondent Erin Moriarty has the latest.',
                'upload_date': '20170604',
                'timestamp': 1496538000,
                'uploader': 'CBSI-NEW',
            },
            'params': {
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_info = self._parse_json(self._html_search_regex(
            r'(?:<ul class="media-list items" id="media-related-items"[^>]*><li data-video-info|<div id="cbsNewsVideoPlayer" data-video-player-options)=\'({.+?})\'',
            webpage, 'video JSON info', default='{}'), video_id, fatal=False)

        if video_info:
            item = video_info['item'] if 'item' in video_info else video_info
        else:
            state = self._parse_json(self._search_regex(
                r'data-cbsvideoui-options=(["\'])(?P<json>{.+?})\1', webpage,
                'playlist JSON info', group='json'), video_id)['state']
            item = state['playlist'][state['pid']]

        return self._extract_video_info(item['mpxRefId'], 'cbsnews')


class CBSNewsLiveVideoIE(InfoExtractor):
    IE_NAME = 'cbsnews:livevideo'
    IE_DESC = 'CBS News Live Videos'
    _VALID_URL = r'https?://(?:www\.)?cbsnews\.com/live/video/(?P<id>[^/?#]+)'

    # Live videos get deleted soon. See http://www.cbsnews.com/live/ for the latest examples
    _TEST = {
        'url': 'http://www.cbsnews.com/live/video/clinton-sanders-prepare-to-face-off-in-nh/',
        'info_dict': {
            'id': 'clinton-sanders-prepare-to-face-off-in-nh',
            'ext': 'mp4',
            'title': 'Clinton, Sanders Prepare To Face Off In NH',
            'duration': 334,
        },
        'skip': 'Video gone',
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        video_info = self._download_json(
            'http://feeds.cbsn.cbsnews.com/rundown/story', display_id, query={
                'device': 'desktop',
                'dvr_slug': display_id,
            })

        formats = self._extract_akamai_formats(video_info['url'], display_id)
        self._sort_formats(formats)

        return {
            'id': display_id,
            'display_id': display_id,
            'title': video_info['headline'],
            'thumbnail': video_info.get('thumbnail_url_hd') or video_info.get('thumbnail_url_sd'),
            'duration': parse_duration(video_info.get('segmentDur')),
            'formats': formats,
        }
