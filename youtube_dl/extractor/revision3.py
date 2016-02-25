# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_iso8601,
    unescapeHTML,
    qualities,
)


class Revision3IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>(?:revision3|testtube|animalist)\.com)/(?P<id>[^/]+(?:/[^/?#]+)?)'
    _TESTS = [{
        'url': 'http://www.revision3.com/technobuffalo/5-google-predictions-for-2016',
        'md5': 'd94a72d85d0a829766de4deb8daaf7df',
        'info_dict': {
            'id': '73034',
            'display_id': 'technobuffalo/5-google-predictions-for-2016',
            'ext': 'webm',
            'title': '5 Google Predictions for 2016',
            'description': 'Google had a great 2015, but it\'s already time to look ahead. Here are our five predictions for 2016.',
            'upload_date': '20151228',
            'timestamp': 1451325600,
            'duration': 187,
            'uploader': 'TechnoBuffalo',
            'uploader_id': 'technobuffalo',
        }
    }, {
        'url': 'http://testtube.com/brainstuff',
        'info_dict': {
            'id': '251',
            'title': 'BrainStuff',
            'description': 'Whether the topic is popcorn or particle physics, you can count on the HowStuffWorks team to explore-and explain-the everyday science in the world around us on BrainStuff.',
        },
        'playlist_mincount': 93,
    }, {
        'url': 'https://testtube.com/dnews/5-weird-ways-plants-can-eat-animals?utm_source=FB&utm_medium=DNews&utm_campaign=DNewsSocial',
        'info_dict': {
            'id': '60163',
            'display_id': 'dnews/5-weird-ways-plants-can-eat-animals',
            'duration': 275,
            'ext': 'webm',
            'title': '5 Weird Ways Plants Can Eat Animals',
            'description': 'Why have some plants evolved to eat meat?',
            'upload_date': '20150120',
            'timestamp': 1421763300,
            'uploader': 'DNews',
            'uploader_id': 'dnews',
        },
    }]
    _PAGE_DATA_TEMPLATE = 'http://www.%s/apiProxy/ddn/%s?domain=%s'
    _API_KEY = 'ba9c741bce1b9d8e3defcc22193f3651b8867e62'

    def _real_extract(self, url):
        domain, display_id = re.match(self._VALID_URL, url).groups()
        page_info = self._download_json(
            self._PAGE_DATA_TEMPLATE % (domain, display_id, domain), display_id)

        if page_info['data']['type'] == 'episode':
            episode_data = page_info['data']
            video_id = compat_str(episode_data['video']['data']['id'])
            video_data = self._download_json(
                'http://revision3.com/api/getPlaylist.json?api_key=%s&codecs=h264,vp8,theora&video_id=%s' % (self._API_KEY, video_id),
                video_id)['items'][0]

            formats = []
            for vcodec, media in video_data['media'].items():
                for quality_id, quality in media.items():
                    if quality_id == 'hls':
                        formats.extend(self._extract_m3u8_formats(
                            quality['url'], video_id, 'mp4',
                            'm3u8_native', m3u8_id='hls', fatal=False))
                    else:
                        formats.append({
                            'url': quality['url'],
                            'format_id': '%s-%s' % (vcodec, quality_id),
                            'tbr': int_or_none(quality.get('bitrate')),
                            'vcodec': vcodec,
                        })
            self._sort_formats(formats)

            preference = qualities(['mini', 'small', 'medium', 'large'])
            thumbnails = [{
                'url': image_url,
                'id': image_id,
                'preference': preference(image_id)
            } for image_id, image_url in video_data.get('images', {}).items()]

            return {
                'id': video_id,
                'display_id': display_id,
                'title': unescapeHTML(video_data['title']),
                'description': unescapeHTML(video_data.get('summary')),
                'timestamp': parse_iso8601(episode_data.get('publishTime'), ' '),
                'author': episode_data.get('author'),
                'uploader': video_data.get('show', {}).get('name'),
                'uploader_id': video_data.get('show', {}).get('slug'),
                'duration': int_or_none(video_data.get('duration')),
                'thumbnails': thumbnails,
                'formats': formats,
            }
        else:
            show_data = page_info['show']['data']
            episodes_data = page_info['episodes']['data']
            num_episodes = page_info['meta']['totalEpisodes']
            processed_episodes = 0
            entries = []
            page_num = 1
            while True:
                entries.extend([self.url_result(
                    'http://%s/%s/%s' % (domain, display_id, episode['slug'])) for episode in episodes_data])
                processed_episodes += len(episodes_data)
                if processed_episodes == num_episodes:
                    break
                page_num += 1
                episodes_data = self._download_json(self._PAGE_DATA_TEMPLATE % (
                    domain, display_id + '/' + compat_str(page_num), domain),
                    display_id)['episodes']['data']

            return self.playlist_result(
                entries, compat_str(show_data['id']),
                show_data.get('name'), show_data.get('summary'))
