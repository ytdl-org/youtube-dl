# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import smuggle_url


class SlidesLiveIE(InfoExtractor):
    _VALID_URL = r'https?://slideslive\.com/(?P<id>[0-9]+)'
    _TESTS = [{
        # video_service_name = YOUTUBE
        'url': 'https://slideslive.com/38902413/gcc-ia16-backend',
        'md5': 'b29fcd6c6952d0c79c5079b0e7a07e6f',
        'info_dict': {
            'id': 'LMtgR8ba0b0',
            'ext': 'mp4',
            'title': 'GCC IA16 backend',
            'description': 'Watch full version of this video at https://slideslive.com/38902413.',
            'uploader': 'SlidesLive Videos - A',
            'uploader_id': 'UC62SdArr41t_-_fX40QCLRw',
            'upload_date': '20170925',
        }
    }, {
        # video_service_name = youtube
        'url': 'https://slideslive.com/38903721/magic-a-scientific-resurrection-of-an-esoteric-legend',
        'only_matching': True,
    }, {
        # video_service_name = url
        'url': 'https://slideslive.com/38922070/learning-transferable-skills-1',
        'only_matching': True,
    }, {
        # video_service_name = vimeo
        'url': 'https://slideslive.com/38921896/retrospectives-a-venue-for-selfreflection-in-ml-research-3',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'https://ben.slideslive.com/player/' + video_id, video_id)
        service_name = video_data['video_service_name'].lower()
        assert service_name in ('url', 'vimeo', 'youtube')
        service_id = video_data['video_service_id']
        info = {
            'id': video_id,
            'thumbnail': video_data.get('thumbnail'),
            'url': service_id,
        }
        if service_name == 'url':
            info['title'] = video_data['title']
        else:
            info.update({
                '_type': 'url_transparent',
                'ie_key': service_name.capitalize(),
                'title': video_data.get('title'),
            })
            if service_name == 'vimeo':
                info['url'] = smuggle_url(
                    'https://player.vimeo.com/video/' + service_id,
                    {'http_headers': {'Referer': url}})
        return info
