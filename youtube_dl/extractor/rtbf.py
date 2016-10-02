# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    ExtractorError,
)


class RTBFIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?rtbf\.be/
        (?:
            video/[^?]+\?.*\bid=|
            ouftivi/(?:[^/]+/)*[^?]+\?.*\bvideoId=|
            auvio/[^/]+\?.*id=
        )(?P<id>\d+)'''
    _TESTS = [{
        'url': 'https://www.rtbf.be/video/detail_les-diables-au-coeur-episode-2?id=1921274',
        'md5': '799f334ddf2c0a582ba80c44655be570',
        'info_dict': {
            'id': '1921274',
            'ext': 'mp4',
            'title': 'Les Diables au coeur (épisode 2)',
            'description': 'Football - Diables Rouges',
            'duration': 3099,
            'upload_date': '20140425',
            'timestamp': 1398456336,
            'uploader': 'rtbfsport',
        }
    }, {
        # geo restricted
        'url': 'http://www.rtbf.be/ouftivi/heros/detail_scooby-doo-mysteres-associes?id=1097&videoId=2057442',
        'only_matching': True,
    }, {
        'url': 'http://www.rtbf.be/ouftivi/niouzz?videoId=2055858',
        'only_matching': True,
    }, {
        'url': 'http://www.rtbf.be/auvio/detail_jeudi-en-prime-siegfried-bracke?id=2102996',
        'only_matching': True,
    }]
    _IMAGE_HOST = 'http://ds1.ds.static.rtbf.be'
    _PROVIDERS = {
        'YOUTUBE': 'Youtube',
        'DAILYMOTION': 'Dailymotion',
        'VIMEO': 'Vimeo',
    }
    _QUALITIES = [
        ('mobile', 'SD'),
        ('web', 'MD'),
        ('high', 'HD'),
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'http://www.rtbf.be/api/media/video?method=getVideoDetail&args[]=%s' % video_id, video_id)

        error = data.get('error')
        if error:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error), expected=True)

        data = data['data']

        provider = data.get('provider')
        if provider in self._PROVIDERS:
            return self.url_result(data['url'], self._PROVIDERS[provider])

        formats = []
        for key, format_id in self._QUALITIES:
            format_url = data.get(key + 'Url')
            if format_url:
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                })

        thumbnails = []
        for thumbnail_id, thumbnail_url in data.get('thumbnail', {}).items():
            if thumbnail_id != 'default':
                thumbnails.append({
                    'url': self._IMAGE_HOST + thumbnail_url,
                    'id': thumbnail_id,
                })

        return {
            'id': video_id,
            'formats': formats,
            'title': data['title'],
            'description': data.get('description') or data.get('subtitle'),
            'thumbnails': thumbnails,
            'duration': data.get('duration') or data.get('realDuration'),
            'timestamp': int_or_none(data.get('created')),
            'view_count': int_or_none(data.get('viewCount')),
            'uploader': data.get('channel'),
            'tags': data.get('tags'),
        }
