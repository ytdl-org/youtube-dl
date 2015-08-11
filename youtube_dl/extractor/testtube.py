from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    qualities,
)


class TestTubeIE(InfoExtractor):
    _VALID_URL = r'https?://testtube\.com/[^/?#]+/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://testtube.com/dnews/5-weird-ways-plants-can-eat-animals?utm_source=FB&utm_medium=DNews&utm_campaign=DNewsSocial',
        'info_dict': {
            'id': '60163',
            'display_id': '5-weird-ways-plants-can-eat-animals',
            'duration': 275,
            'ext': 'webm',
            'title': '5 Weird Ways Plants Can Eat Animals',
            'description': 'Why have some plants evolved to eat meat?',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'DNews',
            'uploader_id': 'dnews',
        },
    }, {
        'url': 'https://testtube.com/iflscience/insane-jet-ski-flipping',
        'info_dict': {
            'id': 'fAGfJ4YjVus',
            'ext': 'mp4',
            'title': 'Flipping Jet-Ski Skills | Outrageous Acts of Science',
            'uploader': 'Science Channel',
            'uploader_id': 'ScienceChannel',
            'upload_date': '20150203',
            'description': 'md5:e61374030015bae1d2e22f096d4769d6',
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        youtube_url = self._html_search_regex(
            r'<iframe[^>]+src="((?:https?:)?//www.youtube.com/embed/[^"]+)"',
            webpage, 'youtube iframe', default=None)
        if youtube_url:
            return self.url_result(youtube_url, 'Youtube', video_id=display_id)

        video_id = self._search_regex(
            r"player\.loadRevision3Item\('video_id',\s*([0-9]+)\);",
            webpage, 'video ID')

        all_info = self._download_json(
            'https://testtube.com/api/getPlaylist.json?api_key=ba9c741bce1b9d8e3defcc22193f3651b8867e62&codecs=h264,vp8,theora&video_id=%s' % video_id,
            video_id)
        info = all_info['items'][0]

        formats = []
        for vcodec, fdatas in info['media'].items():
            for name, fdata in fdatas.items():
                formats.append({
                    'format_id': '%s-%s' % (vcodec, name),
                    'url': fdata['url'],
                    'vcodec': vcodec,
                    'tbr': fdata.get('bitrate'),
                })
        self._sort_formats(formats)

        duration = int_or_none(info.get('duration'))
        images = info.get('images')
        thumbnails = None
        preference = qualities(['mini', 'small', 'medium', 'large'])
        if images:
            thumbnails = [{
                'id': thumbnail_id,
                'url': img_url,
                'preference': preference(thumbnail_id)
            } for thumbnail_id, img_url in images.items()]

        return {
            'id': video_id,
            'display_id': display_id,
            'title': info['title'],
            'description': info.get('summary'),
            'thumbnails': thumbnails,
            'uploader': info.get('show', {}).get('name'),
            'uploader_id': info.get('show', {}).get('slug'),
            'duration': duration,
            'formats': formats,
        }
