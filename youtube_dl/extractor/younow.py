# coding: utf-8
from __future__ import unicode_literals
from datetime import date, datetime

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none, UnsupportedError

MOMENT_URL_FORMAT = 'https://cdn.younow.com/php/api/moment/fetch/id=%s'
STREAM_URL_FORMAT = 'https://hls.younow.com/momentsplaylists/live/%s/%s.m3u8'


class YouNowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?younow\.com/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://www.younow.com/AmandaPadeezy',
        'info_dict': {
            'id': 'AmandaPadeezy',
            'ext': 'mp4',
            'is_live': True,
            'title': 'March 26, 2017',
            'description': 'YouNow is the best way to broadcast live and get an audience to watch you.',
            'thumbnail': 'https://ynassets.s3.amazonaws.com/broadcast/live/157869188/157869188.jpg',
            'tags': ['girls'],
            'categories': ['girls'],
            'uploader': 'AmandaPadeezy',
            'uploader_id': '6716501',
            'uploader_url': 'https://www.younow.com/AmandaPadeezy',
            'creator': 'AmandaPadeezy',
            'formats': [{
                'url': 'https://cdn.younow.com/php/api/broadcast/videoPath/hls=1/broadcastId=157869188/channelId=6716501',
                'ext': 'mp4',
                'protocol': 'm3u8',
            }],
        }
    }

    def _real_extract(self, url):
        username = self._match_id(url)
        data = self._download_json('https://api.younow.com/php/api/broadcast/info/curId=0/user=%s' % (username), username)

        if data.get('media'):
            stream_url = 'https://cdn.younow.com/php/api/broadcast/videoPath/hls=1/broadcastId=%s/channelId=%s' % (
                data.get('broadcastId'),
                data.get('userId'),
            )
        else:
            raise UnsupportedError('Unsupported stream or user is not streaming at this time')

        webpage = self._download_webpage(url, username)
        try:
            uploader = data['user']['profileUrlString']
        except KeyError:
            uploader = username
        try:
            title = data['title']
        except KeyError:
            title = date.today().strftime('%B %d, %Y')

        return {
            'id': uploader,
            'is_live': True,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': data.get('awsUrl'),
            'tags': data.get('tags'),
            'categories': data.get('tags'),
            'uploader': uploader,
            'uploader_id': data.get('userId'),
            'uploader_url': 'https://www.younow.com/%s' % (data['user']['profileUrlString'],),
            'creator': uploader,
            'view_count': int_or_none(data.get('viewers')),
            'like_count': int_or_none(data.get('likes')),
            'formats': [{
                'url': stream_url,
                'ext': 'mp4',
                'protocol': 'm3u8',
            }],
        }


def _moment_to_entry(item):
    title = item.get('text')
    title_type = item.get('titleType')
    if not title:
        if title_type:
            title = 'YouNow %s' % item.get('titleType')
        else:
            title = 'YouNow moment'

    entry = {
        'id': compat_str(item['momentId']),
        'title': title,
        'view_count': int_or_none(item.get('views')),
        'like_count': int_or_none(item.get('likes')),
        'timestamp': int_or_none(item.get('created')),
        'formats': [{
            'url': STREAM_URL_FORMAT % (item['momentId'], item['momentId']),
            'ext': 'mp4',
            'protocol': 'm3u8',
        }],
    }

    try:
        entry['uploader'] = entry['creator'] = item['owner']['name']
        entry['uploader_url'] = 'https://www.younow.com/%s' % (item['owner']['name'],)
        entry['uploader_id'] = item['owner']['userId']
    except KeyError:
        pass

    return entry


class YouNowChannelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?younow\.com/(?P<id>[^/]+)/channel'
    _TEST = {
        'url': 'https://www.younow.com/Kate_Swiz/channel',
        'info_dict': {
            'title': 'Kate_Swiz moments'
        },
        'playlist_count': 6,
    }

    MOMENTS_URL_FORMAT = 'https://cdn.younow.com/php/api/moment/profile/channelId=%s/createdBefore=%d/records=20'

    def _real_extract(self, url):
        entries = []
        username = self._match_id(url)
        user_info = self._download_json('https://api.younow.com/php/api/broadcast/info/curId=0/user=%s' % (username), username, note='Downloading user information')
        channel_id = user_info['userId']
        created_before = 0
        moment_ids = []
        moment_ids_processed = []
        err = False

        while True:
            if created_before:
                cb = datetime.fromtimestamp(created_before)
            else:
                cb = datetime.now()
            info = self._download_json(self.MOMENTS_URL_FORMAT % (channel_id, created_before), username, note='Downloading moments data (created before %s)' % (cb))

            for item in info['items']:
                if item['type'] == 'moment':
                    entry = _moment_to_entry(item)
                    moment_ids_processed.append(entry['id'])
                    entries.append(entry)
                elif item['type'] == 'collection':
                    moment_ids += [compat_str(x) for x in item['momentsIds']]

                try:
                    created_before = int_or_none(item['created'])
                except KeyError:
                    err = True
                    break

            if (err or
                    not info['hasMore'] or
                    'items' not in info or
                    not info['items']):
                break

        for mid in set(moment_ids):
            if mid in moment_ids_processed:
                continue
            item = self._download_json(MOMENT_URL_FORMAT % (mid), mid)
            entries.append(_moment_to_entry(item['item']))

        return self.playlist_result(entries, playlist_title='%s moments' % (username))


class YouNowMomentIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?younow\.com/[^/]+/(?P<id>[^/]+)/[^/]+'
    _TEST = {
        'url': 'https://www.younow.com/GABO.../20712117/36319236/3b316doc/m',
        'info_dict': {
            'id': '20712117',
            'ext': 'mp4',
            'title': 'YouNow capture',
            'view_count': 19,
            'like_count': 0,
            'timestamp': 1490432040,
            'formats': [{
                'url': 'https://hls.younow.com/momentsplaylists/live/20712117/20712117.m3u8',
                'ext': 'mp4',
                'protocol': 'm3u8',
            }],
            'upload_date': '20170325',
            'uploader': 'GABO...',
            'uploader_id': 35917228,
        },
    }

    def _real_extract(self, url):
        mid = self._match_id(url)
        item = self._download_json(MOMENT_URL_FORMAT % (mid), mid)
        return _moment_to_entry(item['item'])
