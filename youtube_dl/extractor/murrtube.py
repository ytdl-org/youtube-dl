# coding: utf-8
from __future__ import unicode_literals
import json

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    try_get,
    unified_strdate,
)


class MurrtubeIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                        (?:
                            murrtube:|
                            https?://murrtube\.net/videos/(?:[a-z0-9\-]+)\-
                        )
                        (?P<id>[a-f0-9]{8}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{12})
                    '''
    _TEST = {
        'url': 'https://murrtube.net/videos/inferno-x-skyler-148b6f2a-fdcc-4902-affe-9c0f41aaaca0',
        'md5': '169f494812d9a90914b42978e73aa690',
        'info_dict': {
            'id': '148b6f2a-fdcc-4902-affe-9c0f41aaaca0',
            'ext': 'mp4',
            'title': 'Inferno X Skyler',
            'description': 'Humping a very good slutty sheppy (roomate)',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 284,
            'uploader': 'Inferno Wolf',
            'upload_date': '20200502',
            'age_limit': 18,
        }
    }

    def _download_gql(self, video_id, op, note=None, fatal=True):
        result = self._download_json(
            "https://murrtube.net/graphql",
            video_id,
            note,
            data=json.dumps(op).encode(),
            headers={
                'Content-Type': "application/json",
            },
            fatal=fatal,
        )
        return result['data']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_gql(video_id, {
            "operationName": "Medium",
            "variables": {
                "id": video_id,
            },
            "query": """query Medium($id: ID!) {
  medium(id: $id) {
    id
    slug
    title
    description
    key
    duration
    commentsCount
    likesCount
    liked
    viewsCount
    publishedAt
    thumbnailKey
    smallThumbnailKey
    tagList
    user {
      id
      slug
      name
      avatar
      __typename
    }
    __typename
  }
}"""})
        meta = data['medium']

        storage_url = 'https://storage.murrtube.net/murrtube/'
        format_url = storage_url + meta['key']
        thumbnail = storage_url + meta['thumbnailKey']

        formats = []
        if determine_ext(format_url) == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                preference=1, fatal=False))
        else:
            formats.append({
                'url': format_url,
            })

        return {
            'id': video_id,
            'title': meta['title'],
            'description': meta.get('description'),
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': int(meta['duration']),
            'uploader': try_get(meta, lambda x: x['user']['name']),
            'upload_date': unified_strdate(meta.get('publishedAt')),
            'view_count': int_or_none(meta.get('viewsCount')),
            'like_count': int_or_none(meta.get('likesCount')),
            'comment_count': int_or_none(meta.get('commentsCount')),
            'tags': meta.get('tagList', []),
            'age_limit': 18,
        }


class MurrtubeUserIE(MurrtubeIE):
    IE_DESC = 'Murrtube user profile'
    _VALID_URL = r'https?://murrtube\.net/(?P<id>[^/]+)/?$'
    _TEST = {
        'url': 'https://murrtube.net/stormy',
        'info_dict': {
            'id': 'stormy',
            'age_limit': 18,
        },
        'playlist_mincount': 28,
    }

    def _real_extract(self, url):
        username = self._match_id(url)
        data = self._download_gql(username, {
            "operationName": "User",
            "variables": {
                "id": username,
            },
            "query": """query User($id: ID!) {
  user(id: $id) {
    id
    public
    chatEnabled
    slug
    name
    avatar
    banner
    bio
    website
    followed
    following
    mediaCount
    followersCount
    followingCount
    likesCount
    blocked
    __typename
  }
}"""},
            "Downloading user info")
        user = data['user']

        page_size = 10
        num_pages = int(user['mediaCount']) // page_size + 1
        entries = []

        for page in range(num_pages):
            data = self._download_gql(username, {
                "operationName": "Media",
                "variables": {
                    "limit": page_size,
                    "offset": page * page_size,
                    "sort": "latest",
                    "userId": user['id'],
                },
                "query": """query Media($q: String, $sort: String, $userId: ID, $offset: Int!, $limit: Int!) {
  media(q: $q, sort: $sort, userId: $userId, offset: $offset, limit: $limit) {
    id
    slug
    title
    description
    previewKey
    thumbnailKey
    smallThumbnailKey
    publishedAt
    duration
    commentsCount
    likesCount
    viewsCount
    tagList
    visibility
    restriction
    user {
      id
      slug
      name
      avatar
      __typename
    }
    __typename
  }
  users(q: $q, fillWithFollowing: false, offset: 0, limit: 2) {
    id
    slug
    name
    avatar
    mediaCount
    __typename
  }
}"""},
                "Downloading page {0}".format(page + 1))
            media = data['media']

            for entry in media:
                entries.append(self.url_result(
                    'murrtube:{0}'.format(entry['id']),
                    MurrtubeIE.ie_key()))

        playlist = self.playlist_result(entries, username)
        playlist['age_limit'] = 18
        return playlist
