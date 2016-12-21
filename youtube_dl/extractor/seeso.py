# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import os.path
from .theplatform import ThePlatformFeedIE
# from .theplatform import ThePlatformBaseIE
from ..utils import (
    sanitized_Request,
    urlencode_postdata,
    int_or_none
)


class SeesoBaseIE(ThePlatformFeedIE):
    def _extract_video_info(self, video_id, auth_token):
        # print "extract_video_info - auth_token: ", auth_token
        # _VIDEO_INFO_URL = 'https://feed.theplatform.com/f/NZILfC/nbcott-prod-all-media?byAvailabilityState=' \
        #                   'available&byId=%s&form=cjson'

        # return self._extract_feed_info(
        #     'NZILfC', 'nbcott-prod-all-media', ('byAvailabilityState=available&byId=%s' % video_id), lambda entry: {
        #         'series': entry.get('nbc-chaos$show'),
        #         'season_number': int_or_none(entry.get('nbc-chaos$seasonNumber')),
        #         'episode': entry.get('nbc-chaos$shortTitle'),
        #         'episode_number': int_or_none(entry.get('nbc-chaos$episodeNumber')),
        #     }, {
        #         'StreamPack': {
        #             'manifest': 'm3u',
        #         }
        #     })

        return self._extract_feed_info(
            'NZILfC', 'nbcott-prod-all-media', 'byId=' + video_id, lambda entry: {
                'series': entry.get('nbc-chaos$show'),
                'season_number': int_or_none(entry.get('nbc-chaos$shortTitle')),
                'episode': entry.get('nbc-chaos$shortTitle'),
                'episode_number': int_or_none(entry.get('nbc-chaos$episodeNumber')),
            }, {
                'Video': {
                    'auth': auth_token,
                }
            })

class SeesoIE(SeesoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?seeso\.com/view/episode/(?P<id>[0-9]+)'
    _TESTS = [{
        'params': {
            'username': '',
            'password': ''
        },
        'url': 'https://www.seeso.com/view/episode/799241283849',
        'info_dict': {
            'id': '799241283849',
            'ext': 'mp4',
            'series': 'Bajillion Dollar Propertie$',
            'title': 'Farsi Lessons',
            'description': ("Amir leads Victoria into a trap, the Bros meet a super obnoxious bro, "
                            "and rival brokers Serge and Gio intimidate Glenn."),
            'thumbnail': 'https://chaosic.akamaized.net/NBCOTT_-_Production/360/907/160831_3092487_Farsi_Lessons.jpg',
        }
    }]

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

        return auth_token

    def _real_extract(self, url):
        video_id = self._match_id(url)
        auth_token = self._login()

        return self._extract_video_info(video_id, auth_token)

        # Use the public unauthenticated API to get the video's info
        # _VIDEO_INFO_URL = 'https://feed.theplatform.com/f/NZILfC/nbcott-prod-all-media?byAvailabilityState=' \
        #                   'available&byId=%s&form=cjson'
        # request = sanitized_Request(_VIDEO_INFO_URL % video_id)
        # json_data = self._download_json(request, video_id)
        # tpf = ThePlatformFeedIE(ThePlatformBaseIE())
        # ThePlatformFeedIE._extract_feed_info(tpf, 'NZILfC', 'VxxJg8Ymh8sE', ('byId=' + video_id), video_id)


        # entry = json_data.get('entries')[0]

        # # DEBUG
        # entry = {}
        #
        # # Template fields
        # title = entry.get("nbc-chaos$shortTitle")
        # series = entry.get("nbc-chaos$show")
        # season_number = entry.get("nbc-chaos$seasonNumber")
        # episode_number = entry.get("nbc-chaos$episodeNumber")
        # thumbnail = entry.get("defaultThumbnailUrl")
        # description = entry.get("nbc-chaos$shortDescription")
        #
        # # Got the show's public URL. Now we need to parse out the videoID
        # public_url_id = os.path.split(entry.get("publicUrl"))[-1]

        # Get the master m3u8 which lists formats
        # m3u8_url = 'https://link.theplatform.com/s/NZILfC/media/{0}?feed=All%20Media%20Feed&auth={1}' \
        #           '&vpaid=script,flash&formats=m3u,mpeg4'.format(public_url_id, auth_token)
        # formats = []

        # pie = ThePlatformIE()
        # # pie._real_extract(m3u8_url)
        # formats = pie._real_extract(m3u8_url)

        for entry in self._extract_m3u8_formats(m3u8_url, video_id, m3u8_id='m3u8', ext='mp4'):
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
