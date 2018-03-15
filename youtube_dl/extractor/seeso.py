# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import os.path
from ..utils import (
    sanitized_Request,
    urlencode_postdata
)


class SeesoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?seeso\.com/view/(episode|movie)/(?P<id>[0-9]+)'
    _TEST = {
        'params': {
            'username': 'emailaddress',
            'password': 'password'
        },
        'url': 'https://www.seeso.com/view/episode/697446467698',
        'info_dict': {
            'id': '697446467698',
            'ext': 'mp4',
            'series': 'Hidden America with Jonah Ray',
            'title': 'CHICAGO: THE SECOND BEST CITY',
            'description': "They call it the Second City and Jonah’s here to find out why. He digs into Chicago’s vast history of corruption as it relates to politics. It’s historical relevance to the Prohibition Era party scene. As well as taking in the city’s famous improv theaters, bars and nightlife.",
            # 'thumbnail': 'https://chaosic.akamaized.net/NBCOTT_-_Production/360/907/160831_3092487_Farsi_Lessons.jpg',
        }
    }

    def _login(self):
        username, password = self._get_login_info()

        if username is None or password is None:
            return

        _API_AUTH_URL = "https://www.seeso.com/api/v3/auth/login"
        auth_json = {
            "username": username,
            "password": password,
            "userOnly": True,
            "isRememberMe": True,
            "isWeb": True
        }

        # Send auth POST request and get token from response
        auth_request = sanitized_Request(_API_AUTH_URL, urlencode_postdata(auth_json))
        auth_response = self._download_json(auth_request, '', note='Getting auth token...')
        auth_token = auth_response.get('user').get('token')

        print("auth_token: ", auth_token)
        return auth_token

    def _real_extract(self, url):
        video_id = self._match_id(url)
        auth_token = self._login()

        # Use the public unauthenticated API to get the video's info
        _VIDEO_INFO_URL = 'https://feed.theplatform.com/f/NZILfC/nbcott-prod-all-media?byAvailabilityState=' \
                          'available&byId=%s&form=cjson'
        request = sanitized_Request(_VIDEO_INFO_URL % video_id)
        json_data = self._download_json(request, video_id)

        entry = json_data.get('entries')[0]

        # Template fields
        series = entry.get("nbc-chaos$show")                    # Show name
        title = entry.get("nbc-chaos$shortTitle")               # Episode Name
        season_number = entry.get("nbc-chaos$seasonNumber")
        episode_number = entry.get("nbc-chaos$episodeNumber")
        thumbnail = entry.get("defaultThumbnailUrl")
        description = entry.get("nbc-chaos$shortDescription")

        # Got the show's public URL. Now we need to parse out the videoID
        public_url_id = os.path.split(entry.get("publicUrl"))[-1]

        # Get the master m3u8 which lists formats
        m3u8_url = 'https://link.theplatform.com/s/NZILfC/media/{0}?feed=All%20Media%20Feed&auth={1}' \
                   '&vpaid=script,flash&formats=m3u,mpeg4'.format(public_url_id, auth_token)
        formats = []
        for entry in self._extract_m3u8_formats(m3u8_url, video_id, m3u8_id='m3u8', ext='ts'):
            formats.append(entry)

        self._sort_formats(formats)

        return {
                'id': video_id,
                'title': title,
                'thumbnail': thumbnail,
                'series': series,
                'season_number': season_number,
                'episode_number': episode_number,
                'description': description,
                'url': '',
                'formats': formats
        }
