# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (int_or_none, sanitized_Request, str_or_none,
                     unified_strdate)


class MindsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?minds\.com/media/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.minds.com/media/100000000000086822',
        'md5': '215a658184a419764852239d4970b045',
        'info_dict': {
            'id': '100000000000086822',
            'ext': 'mp4',
            'title': 'Minds intro sequence',
            'thumbnail': 'https://cdn-cinemr.minds.com/cinemr_com/334128440657580032/thumbnail-00001.png',
            'uploader_id': '100000000000000341',
            'description': '<?xml encoding="utf-8" ?>',
            'upload_date': '20130524',
            'timestamp': 1369404826,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_api_url = 'https://www.minds.com/api/v1/media/%s' % video_id
        token = self._get_cookies(url).get('XSRF-TOKEN')
        headers = {
            'authority': 'www.minds.com',
            'referer': url,
            'x-xsrf-token': token.value if token else '',
        }
        data = self._download_json(video_api_url, video_id, headers=headers,
                                   query={'children': 'false'})
        formats = []
        owner = data.get('ownerObj', {})

        transcodes = data.get('transcodes', {})
        # These keys are the width so keep the highest width last
        keys = sorted(transcodes.keys())

        for format_id in keys:
            is_numeric = re.match('^[0-9]+\.mp4', format_id)
            video_url = transcodes[format_id]
            info = {
                'url': video_url,
                'format_id': format_id,
                'http_headers': headers,
            }
            if is_numeric:
                info['width'] = int(format_id.split('.')[0])
            formats.append(info)

        uploader_id = str_or_none(owner.get('guid') or
                                  data.get('owner_guid') or
                                  owner.get('legacy_guid') or
                                  owner.get('owner_guid'))
        description = str_or_none(data.get('description'))
        if description:
            description = description.strip()
        uploader_url = age_limit = thumbnail = None

        if owner.get('username'):
            uploader_url = 'https://www.minds.com/%s' % owner.get('username')
        if data.get('mature') is True:
            age_limit = 18

        thumbnail_api_url = data.get('thumbnail_src')
        if thumbnail_api_url:
            req = sanitized_Request(thumbnail_api_url)
            req.get_method = lambda: 'HEAD'
            res = self._request_webpage(req, video_id)
            if res.headers.get('content-type', '').startswith('image/'):
                thumbnail = getattr(res, 'url', None)
        tags = data.get('tags', '').strip()
        if isinstance(tags, compat_str) and tags:
            tags = [x.strip() for x in tags.split(',')]
        else:
            tags = None
        category = data.get('category')
        if isinstance(category, compat_str) and category:
            category = [category]
        else:
            category = None

        return {
            'id': video_id,
            'title': data['title'],
            'formats': formats,
            'description': description,
            'license': str_or_none(data.get('license')),
            'creator': str_or_none(owner.get('name') or owner.get('username')),
            'release_date': unified_strdate(data.get('time_created')),
            'timestamp': int_or_none(data.get('time_created')),
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'view_count': int_or_none(data.get('play:count')),
            'like_count': int_or_none(data.get('thumbs:up:count')),
            'dislike_count': int_or_none(data.get('thumbs:down:count')),
            'average_rating': int_or_none(data.get('rating')),
            'age_limit': age_limit,
            'categories': [str_or_none(data.get('category'))],
            'tags': tags,
            # As of 20181020 the API is returning `false` for this value both
            # at top level and within the entity.comments:count path. The only
            # other way to get this is to fetch all comments and count.
            'comment_count': int_or_none(data.get('comments:count')),
            'thumbnail': thumbnail,
        }


class MindsActivityIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?minds\.com/newsfeed/(?P<id>[0-9]+)'

    def _real_extract(self, url):
        guid = self._match_id(url)
        api_url = 'https://www.minds.com/api/v1/newsfeed/single/%s' % guid
        token = self._get_cookies(url).get('XSRF-TOKEN')
        headers = {
            'authority': 'www.minds.com',
            'referer': url,
            'x-xsrf-token': token.value if token else '',
        }
        data = self._download_json(api_url, guid, headers=headers)
        return self.url_result('https://www.minds.com/media/%s' % data['activity']['entity_guid'])


class MindsChannelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?minds\.com/(?!newsfeed|media|api)(?P<id>[^/]+)'

    def _real_extract(self, url):
        channel_name = self._match_id(url)
        api_url = 'https://www.minds.com/api/v1/channel/%s' % channel_name
        token = self._get_cookies(url).get('XSRF-TOKEN')
        headers = {
            'authority': 'www.minds.com',
            'referer': url,
            'x-xsrf-token': token.value if token else '',
        }
        data = self._download_json(api_url, channel_name, headers=headers)
        channel = data.get('channel', {})
        params = {'limit': 12, 'offset': ''}
        api_url = 'https://www.minds.com/api/v1/newsfeed/personal/%s' % channel['guid']
        entries = []
        while True:
            data = self._download_json(api_url, channel['guid'],
                                       headers=headers, query=params)
            activity = data.get('activity', [])
            if len(activity) == 0 or not data.get('load-next'):
                break
            for info in activity:
                if info.get('custom_type') != 'video':
                    continue
                entries.append(self.url_result('https://www.minds.com/media/%s' % info['entity_guid']))
            params['offset'] = data['load-next']
        return self.playlist_result(entries,
                                    playlist_title='%s activity' % channel_name)
