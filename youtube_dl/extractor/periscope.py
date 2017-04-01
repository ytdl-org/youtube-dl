# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    unescapeHTML,
)


class PeriscopeBaseIE(InfoExtractor):
    def _call_api(self, method, query, item_id):
        return self._download_json(
            'https://api.periscope.tv/api/v2/%s' % method,
            item_id, query=query)


class PeriscopeIE(PeriscopeBaseIE):
    IE_DESC = 'Periscope'
    IE_NAME = 'periscope'
    _VALID_URL = r'https?://(?:www\.)?(?:periscope|pscp)\.tv/[^/]+/(?P<id>[^/?#]+)'
    # Alive example URLs can be found here http://onperiscope.com/
    _TESTS = [{
        'url': 'https://www.periscope.tv/w/aJUQnjY3MjA3ODF8NTYxMDIyMDl2zCg2pECBgwTqRpQuQD352EMPTKQjT4uqlM3cgWFA-g==',
        'md5': '65b57957972e503fcbbaeed8f4fa04ca',
        'info_dict': {
            'id': '56102209',
            'ext': 'mp4',
            'title': 'Bec Boop - 🚠✈️🇬🇧 Fly above #London in Emirates Air Line cable car at night 🇬🇧✈️🚠 #BoopScope 🎀💗',
            'timestamp': 1438978559,
            'upload_date': '20150807',
            'uploader': 'Bec Boop',
            'uploader_id': '1465763',
        },
        'skip': 'Expires in 24 hours',
    }, {
        'url': 'https://www.periscope.tv/w/1ZkKzPbMVggJv',
        'only_matching': True,
    }, {
        'url': 'https://www.periscope.tv/bastaakanoggano/1OdKrlkZZjOJX',
        'only_matching': True,
    }, {
        'url': 'https://www.periscope.tv/w/1ZkKzPbMVggJv',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=([\'"])(?P<url>(?:https?:)?//(?:www\.)?periscope\.tv/(?:(?!\1).)+)\1', webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        token = self._match_id(url)

        broadcast_data = self._call_api(
            'getBroadcastPublic', {'broadcast_id': token}, token)
        broadcast = broadcast_data['broadcast']
        status = broadcast['status']

        user = broadcast_data.get('user', {})

        uploader = broadcast.get('user_display_name') or user.get('display_name')
        uploader_id = (broadcast.get('username') or user.get('username') or
                       broadcast.get('user_id') or user.get('id'))

        title = '%s - %s' % (uploader, status) if uploader else status
        state = broadcast.get('state').lower()
        if state == 'running':
            title = self._live_title(title)
        timestamp = parse_iso8601(broadcast.get('created_at'))

        thumbnails = [{
            'url': broadcast[image],
        } for image in ('image_url', 'image_url_small') if broadcast.get(image)]

        stream = self._call_api(
            'getAccessPublic', {'broadcast_id': token}, token)

        formats = []
        for format_id in ('replay', 'rtmp', 'hls', 'https_hls'):
            video_url = stream.get(format_id + '_url')
            if not video_url:
                continue
            f = {
                'url': video_url,
                'ext': 'flv' if format_id == 'rtmp' else 'mp4',
            }
            if format_id != 'rtmp':
                f['protocol'] = 'm3u8_native' if state in ('ended', 'timed_out') else 'm3u8'
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': broadcast.get('id') or token,
            'title': title,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'thumbnails': thumbnails,
            'formats': formats,
        }


class PeriscopeUserIE(PeriscopeBaseIE):
    _VALID_URL = r'https?://(?:www\.)?(?:periscope|pscp)\.tv/(?P<id>[^/]+)/?$'
    IE_DESC = 'Periscope user videos'
    IE_NAME = 'periscope:user'

    _TEST = {
        'url': 'https://www.periscope.tv/LularoeHusbandMike/',
        'info_dict': {
            'id': 'LularoeHusbandMike',
            'title': 'LULAROE HUSBAND MIKE',
            'description': 'md5:6cf4ec8047768098da58e446e82c82f0',
        },
        # Periscope only shows videos in the last 24 hours, so it's possible to
        # get 0 videos
        'playlist_mincount': 0,
    }

    def _real_extract(self, url):
        user_name = self._match_id(url)

        webpage = self._download_webpage(url, user_name)

        data_store = self._parse_json(
            unescapeHTML(self._search_regex(
                r'data-store=(["\'])(?P<data>.+?)\1',
                webpage, 'data store', default='{}', group='data')),
            user_name)

        user = list(data_store['UserCache']['users'].values())[0]['user']
        user_id = user['id']
        session_id = data_store['SessionToken']['public']['broadcastHistory']['token']['session_id']

        broadcasts = self._call_api(
            'getUserBroadcastsPublic',
            {'user_id': user_id, 'session_id': session_id},
            user_name)['broadcasts']

        broadcast_ids = [
            broadcast['id'] for broadcast in broadcasts if broadcast.get('id')]

        title = user.get('display_name') or user.get('username') or user_name
        description = user.get('description')

        entries = [
            self.url_result(
                'https://www.periscope.tv/%s/%s' % (user_name, broadcast_id))
            for broadcast_id in broadcast_ids]

        return self.playlist_result(entries, user_id, title, description)
