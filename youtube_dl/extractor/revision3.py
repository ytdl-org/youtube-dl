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
            'id': '71089',
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
        # Show
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
            'id': '58227',
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
    }, {
        'url': 'http://testtube.com/tt-editors-picks/the-israel-palestine-conflict-explained-in-ten-min',
        'info_dict': {
            'id': '71618',
            'ext': 'mp4',
            'display_id': 'tt-editors-picks/the-israel-palestine-conflict-explained-in-ten-min',
            'title': 'The Israel-Palestine Conflict Explained in Ten Minutes',
            'description': 'If you\'d like to learn about the struggle between Israelis and Palestinians, this video is a great place to start',
            'uploader': 'Editors\' Picks',
            'uploader_id': 'tt-editors-picks',
            'timestamp': 1453309200,
            'upload_date': '20160120',
        },
        'add_ie': ['Youtube'],
    }, {
        # Tag
        'url': 'http://testtube.com/tech-news',
        'info_dict': {
            'id': '21018',
            'title': 'tech news',
        },
        'playlist_mincount': 9,
    }]
    _PAGE_DATA_TEMPLATE = 'http://www.%s/apiProxy/ddn/%s?domain=%s'
    _API_KEY = 'ba9c741bce1b9d8e3defcc22193f3651b8867e62'

    def _real_extract(self, url):
        domain, display_id = re.match(self._VALID_URL, url).groups()
        site = domain.split('.')[0]
        page_info = self._download_json(
            self._PAGE_DATA_TEMPLATE % (domain, display_id, domain), display_id)

        page_data = page_info['data']
        page_type = page_data['type']
        if page_type in ('episode', 'embed'):
            show_data = page_data['show']['data']
            page_id = compat_str(page_data['id'])
            video_id = compat_str(page_data['video']['data']['id'])

            preference = qualities(['mini', 'small', 'medium', 'large'])
            thumbnails = [{
                'url': image_url,
                'id': image_id,
                'preference': preference(image_id)
            } for image_id, image_url in page_data.get('images', {}).items()]

            info = {
                'id': page_id,
                'display_id': display_id,
                'title': unescapeHTML(page_data['name']),
                'description': unescapeHTML(page_data.get('summary')),
                'timestamp': parse_iso8601(page_data.get('publishTime'), ' '),
                'author': page_data.get('author'),
                'uploader': show_data.get('name'),
                'uploader_id': show_data.get('slug'),
                'thumbnails': thumbnails,
                'extractor_key': site,
            }

            if page_type == 'embed':
                info.update({
                    '_type': 'url_transparent',
                    'url': page_data['video']['data']['embed'],
                })
                return info

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

            info.update({
                'title': unescapeHTML(video_data['title']),
                'description': unescapeHTML(video_data.get('summary')),
                'uploader': video_data.get('show', {}).get('name'),
                'uploader_id': video_data.get('show', {}).get('slug'),
                'duration': int_or_none(video_data.get('duration')),
                'formats': formats,
            })
            return info
        else:
            list_data = page_info[page_type]['data']
            episodes_data = page_info['episodes']['data']
            num_episodes = page_info['meta']['totalEpisodes']
            processed_episodes = 0
            entries = []
            page_num = 1
            while True:
                entries.extend([{
                    '_type': 'url',
                    'url': 'http://%s%s' % (domain, episode['path']),
                    'id': compat_str(episode['id']),
                    'ie_key': 'Revision3',
                    'extractor_key': site,
                } for episode in episodes_data])
                processed_episodes += len(episodes_data)
                if processed_episodes == num_episodes:
                    break
                page_num += 1
                episodes_data = self._download_json(self._PAGE_DATA_TEMPLATE % (
                    domain, display_id + '/' + compat_str(page_num), domain),
                    display_id)['episodes']['data']

            return self.playlist_result(
                entries, compat_str(list_data['id']),
                list_data.get('name'), list_data.get('summary'))
