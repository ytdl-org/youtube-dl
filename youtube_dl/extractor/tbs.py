# coding: utf-8
from __future__ import unicode_literals

import re

from .turner import TurnerBaseIE
from ..utils import (
    float_or_none,
    int_or_none,
    strip_or_none,
)


class TBSIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?(?P<site>tbs|tntdrama)\.com/(?:movies|shows/[^/]+/(?:clips|season-\d+/episode-\d+))/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'http://www.tntdrama.com/shows/the-alienist/clips/monster',
        'info_dict': {
            'id': '8d384cde33b89f3a43ce5329de42903ed5099887',
            'ext': 'mp4',
            'title': 'Monster',
            'description': 'Get a first look at the theatrical trailer for TNT’s highly anticipated new psychological thriller The Alienist, which premieres January 22 on TNT.',
            'timestamp': 1508175329,
            'upload_date': '20171016',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://www.tbs.com/shows/search-party/season-1/episode-1/explicit-the-mysterious-disappearance-of-the-girl-no-one-knew',
        'only_matching': True,
    }, {
        'url': 'http://www.tntdrama.com/movies/star-wars-a-new-hope',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        site, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)
        video_data = self._parse_json(self._search_regex(
            r'<script[^>]+?data-drupal-selector="drupal-settings-json"[^>]*?>({.+?})</script>',
            webpage, 'drupal setting'), display_id)['turner_playlist'][0]

        media_id = video_data['mediaID']
        title = video_data['title']

        streams_data = self._download_json(
            'http://medium.ngtv.io/media/%s/tv' % media_id,
            media_id)['media']['tv']
        duration = None
        chapters = []
        formats = []
        for supported_type in ('unprotected', 'bulkaes'):
            stream_data = streams_data.get(supported_type, {})
            m3u8_url = stream_data.get('secureUrl') or stream_data.get('url')
            if not m3u8_url:
                continue
            if stream_data.get('playlistProtection') == 'spe':
                m3u8_url = self._add_akamai_spe_token(
                    'http://www.%s.com/service/token_spe' % site,
                    m3u8_url, media_id, {
                        'url': url,
                        'site_name': site[:3].upper(),
                        'auth_required': video_data.get('authRequired') == '1',
                    })
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, media_id, 'mp4', m3u8_id='hls', fatal=False))

            duration = float_or_none(stream_data.get('totalRuntime') or video_data.get('duration'))

            if not chapters:
                for chapter in stream_data.get('contentSegments', []):
                    start_time = float_or_none(chapter.get('start'))
                    duration = float_or_none(chapter.get('duration'))
                    if start_time is None or duration is None:
                        continue
                    chapters.append({
                        'start_time': start_time,
                        'end_time': start_time + duration,
                    })
        self._sort_formats(formats)

        thumbnails = []
        for image_id, image in video_data.get('images', {}).items():
            image_url = image.get('url')
            if not image_url or image.get('type') != 'video':
                continue
            i = {
                'id': image_id,
                'url': image_url,
            }
            mobj = re.search(r'(\d+)x(\d+)', image_url)
            if mobj:
                i.update({
                    'width': int(mobj.group(1)),
                    'height': int(mobj.group(2)),
                })
            thumbnails.append(i)

        return {
            'id': media_id,
            'title': title,
            'description': strip_or_none(video_data.get('descriptionNoTags') or video_data.get('shortDescriptionNoTags')),
            'duration': duration,
            'timestamp': int_or_none(video_data.get('created')),
            'season_number': int_or_none(video_data.get('season')),
            'episode_number': int_or_none(video_data.get('episode')),
            'cahpters': chapters,
            'thumbnails': thumbnails,
            'formats': formats,
        }
