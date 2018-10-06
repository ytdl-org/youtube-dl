from __future__ import unicode_literals

from .common import InfoExtractor


class VideofyMeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.videofy\.me/.+?|p\.videofy\.me/v)/(?P<id>\d+)(&|#|$)'
    IE_NAME = 'videofy.me'

    _TESTS = [{
        'url': 'https://www.videofy.me/v/24582',
        'md5': '1e46140bacdae8959827903cecd054d9',
        'info_dict': {
            'id': '24582',
            'ext': 'mp4',
            'title': 'The VideofyMe app demo!',
            'description': 'This is VideofyMe.',
            'upload_date': '20120607',
            'timestamp': 1339070671,
            'uploader': 'oskarglauser',
            'uploader_id': 7010,
            'view_count': int,
        },
    }, {
        'url': 'https://www.videofy.me/v/2975905',
        'md5': '79ad4498ab14dec72e815a8f85c7641c',
        'info_dict': {
            'id': '2975905',
            'ext': 'mp4',
            'title': 'But',
            'description': '',
            'upload_date': '20180126',
            'timestamp': 1516931131,
            'uploader': 'iamatlien',
            'uploader_id': 1798214,
            'view_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        page = self._download_webpage(url, video_id)

        video_info = self._search_json_ld(page, video_id)

        uploader_id = self._download_json('https://www.videofy.me/wp-json/wp/v2/poss/%s' % video_id, video_id, fatal=False)
        uploader_id = uploader_id.get('author') if uploader_id is not False else None
        uploader_name = self._download_json('https://www.videofy.me/wp-json/wp/v2/users/%s' % uploader_id, uploader_id, fatal=False)
        uploader_name = uploader_name.get('name') if uploader_name is not False else None

        video_info['id'] = video_id
        video_info['uploader_id'] = uploader_id
        video_info['uploader'] = uploader_name

        return video_info
