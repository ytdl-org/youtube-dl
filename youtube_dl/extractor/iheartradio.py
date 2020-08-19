# coding: utf-8
from __future__ import unicode_literals

import json
import re
import uuid

from .common import InfoExtractor

from ..compat import compat_str

from numbers import Number

from ..utils import (
    clean_html,
    str_or_none,
    urlencode_postdata
)


class IHeartRadioPodcastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?iheart\.com/podcast/\d+-(?P<pod_title>[\w-]+)-(?P<pod_id>\d+)(?:/episode/(?P<title>[\w-]+)-(?P<id>\d+))?/?(?:embed=true)?'
    IE_NAME = "iheartradio:podcast"
    _TESTS = [{
        'url': 'https://www.iheart.com/podcast/1119-it-could-happen-here-30717896/',
        'info_dict': {
            'title': 'It Could Happen Here',
            'description': 'md5:5842117412a967eb0b01f8088eb663e2',
            'id': '30717896',
            'display_id': 'it-could-happen-here'
        },
        'playlist_count': 11
    }, {
        'url': 'https://www.iheart.com/podcast/105-behind-the-bastards-29236323/episode/part-one-alexander-lukashenko-the-dictator-70346499/?embed=true',
        # IHeartRadio has ads, I can't tell if they're custom or not,
        # so the MD5 hash might be inconsistent
        'md5': 'c8609c92c8688dcb69d8541042b8abca',
        'info_dict': {
            'id': '70346499',
            'ext': 'mp3',
            'title': 'Part One: Alexander Lukashenko: The Dictator of Belarus',
            'thumbnail': 'https://i.iheart.com/v3/catalog/podcast/29236323',
            'description': 'md5:96cc7297b3a5a9ebae28643801c96fae',
            'timestamp': 1597741200,
            'upload_date': '20200818',
            'duration': 4156,
            'display_id': 'part-one-alexander-lukashenko-the-dictator'
        }
    }]

    # To get the audio files, we have to use their internal API
    def _real_extract(self, url):
        match = re.match(self._VALID_URL, url)

        podcast_display_id = match.group('pod_title')
        podcast_id = match.group('pod_id')

        episode_display_id = match.group('title')
        episode_id = match.group('id')

        current_id = str_or_none(episode_id, default=podcast_id)

        is_single_episode = episode_id is not None

        # Don't load embed pages
        url = url.replace('?embed=true', '')
        webpage = self._download_webpage(url, current_id)

        # Register anonymous user, same behavior as web app
        random_device_id = compat_str(uuid.uuid4())
        random_oauth_id = compat_str(uuid.uuid4())

        register_user_values = urlencode_postdata({
            'accessToken': 'anon',
            'accessTokenType': 'anon',
            'deviceId': random_device_id,
            'deviceName': "web-desktop",
            'host': "webapp.WW",
            'oauthUuid': random_oauth_id,
            'userName': 'anon' + random_oauth_id
        })
        temp_user = self._download_json(
            'https://ww.api.iheart.com/api/v1/account/loginOrCreateOauthUser',
            current_id, "Registering temporary user", data=register_user_values,
            headers={'Accept': 'application/json, text/plain, */*',
                     'X-hostName': 'webapp.WW'})

        session_id = temp_user['sessionId']
        profile_id = temp_user['profileId']

        if (not is_single_episode):
            episode_ids = []
            for episode in self._get_all_episodes(podcast_id, temp_user):
                episode_ids.append(episode['id'])
        else:
            episode_ids = [episode_id]

        streams_values = json.dumps({
            'contentIds': episode_ids,
            'hostName': 'webapp.WW',
            'playedFrom': 6,  # Not sure about the meaning behind this, Firefox uses 6
            'stationId': compat_str(podcast_id),
            'stationType': 'PODCAST'
        }).encode('utf-8')
        stream_info = self._download_json(
            'https://ww.api.iheart.com/api/v2/playback/streams',
            current_id, "Requesting stream info", data=streams_values,
            headers={'Content-Type': 'application/json;charset=utf-8',
                     'X-Session-Id': session_id,
                     'X-User-Id': profile_id})

        # self.to_screen(stream_info)

        # Extract info from webpage (entirely optional)

        podcast_title = self._search_regex(
            r'<h1[^>]*>(?P<title>[^<]*)<\/h1>',
            webpage, 'title', fatal=False) or self._og_search_title(webpage)

        podcast_description = self._search_regex(
            r'<div class="[^"]*Body2-Description[^"]*">(?:<\/?span[^>]*>)*(?P<description>[^<]*)',
            webpage, 'description', fatal=False)

        if (is_single_episode):
            return self._real_extract_single(stream_info['items'][0],
                                             episode_display_id, podcast_id,
                                             podcast_title)
        else:
            entries = []
            for item in stream_info['items']:
                entries.append(self._real_extract_single(item,
                                                         episode_display_id,
                                                         podcast_id,
                                                         podcast_title))
            return {
                'title': podcast_title,
                'description': podcast_description,
                'id': podcast_id,
                'display_id': podcast_display_id,
                '_type': 'playlist',
                'entries': entries
            }

    def _real_extract_single(self, item_info, display_id, podcast_id, podcast_title):
        content_info = item_info['content']

        thumbnails = [{
            'url': 'https://i.iheart.com/v3/catalog/podcast/%s' % podcast_id,
            'width': 3000,
            'height': 3000
        }]

        # They have an API that dynamically generates images of a needed size
        # This is a list of "standard" sizes which are used by the web app
        for size in [75, 240, 480]:
            thumbnails.append({
                'url': 'https://i.iheart.com/v3/catalog/podcast/%(id)s?ops=fit(%(size)d, %(size)d)' % {
                    'id': podcast_id, 'size': size},
                'width': size,
                'height': size
            })

        # Release date timestamp is in milliseconds
        release_date = content_info.get('startDate')
        if (isinstance(release_date, Number) and release_date > 2000000000):
            release_date /= 1000

        # Remove analytics from stream URL (optional)
        streamUrl = item_info['streamUrl']
        streamUrl = re.sub(r'(?:www\.)?podtrac\.com/pts/redirect\.[\w]*/', '', streamUrl)
        streamUrl = re.sub(r'chtbl\.com/track/[\w]*/', '', streamUrl)
        streamUrl = re.sub(r'\?source=[\w]*', '', streamUrl)

        return {
            'id': compat_str(content_info['id']),
            'display_id': display_id,
            'title': content_info['title'],
            'description': clean_html(content_info.get('description')),
            'url': streamUrl,
            'duration': content_info.get('duration'),
            'timestamp': release_date,
            'thumbnails': thumbnails,
            'series': podcast_title
        }

    def _get_all_episodes(self, podcast_id, temp_user):
        episodes_info = self._download_json(
            'https://ww.api.iheart.com/api/v3/podcast/podcasts/%s/episodes?limit=100000' % (
                podcast_id),
            podcast_id, "Requesting episodes info",
            headers={'Accept': 'application/json, text/plain, */*',
                     'X-hostName': 'webapp.WW',
                     'X-Ihr-Profile-Id': temp_user['profileId']})

        return episodes_info['data']
