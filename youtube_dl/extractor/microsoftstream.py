# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (ExtractorError, update_url_query, merge_dicts)


class MicrosoftStreamBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://web.microsoftstream.com/?noSignUpCheck=1'     # expect redirection
    _ACCESS_TOKEN = None  # A JWT token
    _API_GATEWAY = None

    def is_logged_in(self, webpage):
        """
         This test is based on the fact that Microsoft Stream will redirect unauthenticated users
        """
        return '<title>Microsoft Stream</title>' in webpage

    def _real_initialize(self):
        username, password = self._get_login_info()

        if username is not None or password is not None:
            raise ExtractorError('MicrosoftStream Extractor does not support username/password log-in at the moment. Please use cookies log-in instead. See https://github.com/ytdl-org/youtube-dl/blob/master/README.md#how-do-i-pass-cookies-to-youtube-dl for more information')

    """
     Extraction Helper
    """

    def _extract_access_token(self, webpage):
        """
         Extract the JWT access token with Regex
        """
        self._ACCESS_TOKEN = self._html_search_regex(r"\"AccessToken\":\"(?P<AccessToken>.+?)\"", webpage, 'AccessToken')
        return self._ACCESS_TOKEN

    def _extract_api_gateway(self, webpage):
        """
         Extract the API gateway with Regex
        """
        self._API_GATEWAY = self._html_search_regex(r"\"ApiGatewayUri\":\"(?P<APIGateway>.+?)\"", webpage, 'APIGateway')
        return self._API_GATEWAY

    """
     Common getters
    """
    @property
    def api_gateway(self):
        """
         Return the start of an API endoint, like "https://aaea-1.api.microsoftstream.com/api/"
        """
        if self._API_GATEWAY is None:
            raise ExtractorError('API gateway is None. Did you forget to call "_extract_api_gateway"?')
        return self._API_GATEWAY

    @property
    def access_token(self):
        if self._ACCESS_TOKEN is None:
            raise ExtractorError('Access token is None. Did you forget to call "_extract_access_token"?')
        return self._ACCESS_TOKEN

    @property
    def headers(self):
        return {'Authorization': 'Bearer %s' % self.access_token}

    """
     Utils function
    """

    def _determine_protocol(self, mime):
        """
         A switch board for the MIME type provided from the API endpoint.
        """
        if mime in ['application/dash+xml']:
            return 'http_dash_segments'
        elif mime in ['application/vnd.apple.mpegurl']:
            return 'm3u8'
        else:
            return None

    """
     Remapper

     Remap data into correct field
    """

    def _remap_thumbnails(self, thumbnail_dict_list):
        output = []
        preference_index = ['extraSmall', 'small', 'medium', 'large']

        for _, key in enumerate(thumbnail_dict_list):
            output.append({
                'preference': preference_index.index(key),
                'url': thumbnail_dict_list.get(key).get('url')
            })
        return output

    def _remap_playback(self, master_playlist_urls, video_id=None):
        """
         A parser for the HLS and MPD playlists from the API endpoint.
        """
        output = []

        for master_playlist_url in master_playlist_urls:
            protocol = self._determine_protocol(master_playlist_url['mimeType'])
            # Handle HLS Master playlist
            if protocol == 'm3u8':
                varient_playlists = self._extract_m3u8_formats(master_playlist_url['playbackUrl'], video_id=video_id, headers=self.headers)

            # For MPEG-DASH Master playlists
            elif protocol == 'http_dash_segments':
                varient_playlists = self._extract_mpd_formats(master_playlist_url['playbackUrl'], video_id=video_id, headers=self.headers)

            # For other Master playlists (like Microsoft Smooth Streaming)
            else:
                self.to_screen('Found unresolvable stream with format: %s' % master_playlist_url['mimeType'])
                continue

            # Patching the "Authorization" header
            for varient_playlist in varient_playlists:
                varient_playlist['http_headers'] = self.headers
                output.append(varient_playlist)
        return output

    def _remap_subtitle(self, tracks, video_id, is_auto_generated):
        """
         An internal method for filtering and remapping text tracks
        """
        if type(is_auto_generated) is not bool:
            raise ExtractorError('Unexpected variable "is_auto_generated" type: must be a Boolean')

        subtitle_subset = {}

        for track in tracks:
            track_language = track.get('language')           # The track language must have a language code.

            if track.get('autoGenerated') is is_auto_generated:
                if track_language not in subtitle_subset:
                    subtitle_subset[track_language] = []     # Scaffold an empty list for the object to insert into

                # Since the subtitle is token protected, a get request will fire here.
                data = self._download_webpage(url_or_request=track.get('url'), video_id=video_id, headers=self.headers)
                subtitle_subset[track_language].append({'data': data, "ext": "vtt"})

        return subtitle_subset

    def _remap_video(self, video):
        return {
            'id': video['id'],
            'title': video['name'],
            'description': video.get('description'),
            'uploader': video.get('creator').get('name'),
            'thumbnails': self._remap_thumbnails(video.get('posterImage') or []),
            'formats': self._remap_playback(video['playbackUrls'], video_id=video['id']),
            'is_live': False
        }
    """
    Formatter
    """

    def _format_texttrack_endpoint(self, video_id):
        return "%s/videos/%s/texttracks?api-version=1.4-private" % (self.api_gateway, video_id)

    def _request_texttracks(self, video_id):
        """
         Make an additional request to Microsoft Stream for the subtitle and auto-caption
        """
        self._TEXTTRACKS_RESPONSE = self._download_json(self._format_texttrack_endpoint(video_id), video_id, headers=self.headers).get('value')
        return self._TEXTTRACKS_RESPONSE


class MicrosoftStreamIE(MicrosoftStreamBaseIE):
    """
     Extractor for single Microsoft Stream video
    """
    IE_NAME = 'microsoftstream'
    _VALID_URL = r'https?://(?:(?:web|www)\.)?microsoftstream\.com/video/(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'  # https://regex101.com/r/K1mlgK/1/
    _NETRC_MACHINE = 'microsoftstream'
    _TEXTTRACKS_RESPONSE = None
    _VIDEO_ID = None

    _TESTS = [{
        'url': 'https://web.microsoftstream.com/video/c883c6a5-9895-4900-9a35-62f4b5d506c9',
        'info_dict': {
            'id': 'c883c6a5-9895-4900-9a35-62f4b5d506c9',
            'ext': 'mp4',
            'title': 'Webinar for Researchers: Use of GitLab',
            'thumbnail': r're:^https?://.*$'
        },
        'skip': 'Requires Microsoft 365 account credentials',
    }, {
        'url': 'https://www.microsoftstream.com/video/1541f3f9-7fed-4901-ae70-0f7cb775679f',
        'only_matching': True,
    }]

    """
     Getters

     The following getters include helpful message to prompt developers for potential errors.
    """

    @property
    def video_id(self):
        if self._VIDEO_ID is None:
            raise('Variable "_VIDEO_ID" is not defined. Did you make the main extraction call?')
        return self._VIDEO_ID

    @property
    def media_info_endpoint(self):
        return "%s/videos/%s?$expand=creator,tokens,status,liveEvent,extensions&api-version=1.4-private" % (self.api_gateway, self.video_id)

    def _get_subtitles(self, tracks=None):                        # Fulfill abstract method
        tracks = self._TEXTTRACKS_RESPONSE if tracks is None else tracks
        return self._remap_subtitle(tracks, is_auto_generated=False, video_id=self.video_id)

    def _get_automatic_captions(self, tracks=None):               # Fulfill abstract method
        tracks = self._TEXTTRACKS_RESPONSE if tracks is None else tracks
        return self._remap_subtitle(tracks, is_auto_generated=True, video_id=self.video_id)

    def _real_extract(self, url):
        self._VIDEO_ID = self._match_id(url)

        webpage = self._download_webpage(url, self.video_id)
        if not self.is_logged_in(webpage):
            return self.raise_login_required()

        # Extract access token from webpage
        self._extract_access_token(webpage)
        self._extract_api_gateway(webpage)

        # "GET" api for video information
        video = self._download_json(self.media_info_endpoint, self.video_id, headers=self.headers)
        texttracks = self._request_texttracks(self.video_id)

        return merge_dicts(self._remap_video(video), {
            'subtitles': self._get_subtitles(texttracks),
            'automatic_captions': self._get_automatic_captions(texttracks),
        })


class MicrosoftStreamChannelIE(MicrosoftStreamBaseIE):
    """
     Extractor for single channel of Microsoft Stream video
    """
    IE_NAME = 'microsoftstream:channel'
    _VALID_URL = r'https?://(?:(?:web|www)\.)?microsoftstream\.com/channel/(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'  # https://regex101.com/r/K1mlgK/1/
    _NETRC_MACHINE = 'microsoftstream'
    _CHANNEL_ID = None

    _TESTS = [{
        'url': 'https://web.microsoftstream.com/channel/c883c6a5-9895-4900-9a35-62f4b5d506c9',
        'only_matching': True,
    }, {
        'url': 'https://www.microsoftstream.com/channel/0ceffe58-07b1-4098-8ed9-a15f4e8231f7',
        'only_matching': True,
    }]

    def _format_channel_video_endpoint(self, skip=0, top=100):
        parameters = {
            '$top': top,
            '$skip': skip,
            '$expand': 'creator,events',
            '$orderby': 'created asc',
            'api-version': '1.4-private'
        }

        return update_url_query('%schannels/%s/videos' % (self.api_gateway, self._CHANNEL_ID), parameters)

    def _iterate_video(self, video):
        subtitle_dict = {}

        if (self._downloader.params.get('writesubtitles', False)
                or self._downloader.params.get('writeautomaticsub', False)
                or self._downloader.params.get('listsubtitles')):
            texttracks = self._request_texttracks(video['id'])

        if (self._downloader.params.get('writesubtitles', False)
                or self._downloader.params.get('listsubtitles')):
            subtitle_dict['subtitles'] = self._remap_subtitle(texttracks, video_id=video['id'], is_auto_generated=False)

        if (self._downloader.params.get('writeautomaticsub', False)
                or self._downloader.params.get('listsubtitles')):
            subtitle_dict['automatic_captions'] = self._remap_subtitle(texttracks, video_id=video['id'], is_auto_generated=False)

        return merge_dicts(self._remap_video(video), subtitle_dict)

    def _fetch_video(self):
        found_all_video = False
        current_skip = 0
        top = 100
        all_video = []

        while found_all_video is False:
            video_info_endpoint = self._format_channel_video_endpoint(current_skip, top)
            channel_video_subset = self._download_json(video_info_endpoint, self._CHANNEL_ID, headers=self.headers)['value']

            for video in channel_video_subset:
                all_video.append(self._iterate_video(video))           # Remap the video

            found_all_video = bool(len(channel_video_subset) < top)  # Break out from the iteration if all content is downloaded.
            current_skip += top                                      # Adjust starting position

        return all_video

    def _real_extract(self, url):
        self._CHANNEL_ID = self._match_id(url)

        webpage = self._download_webpage(url, self._CHANNEL_ID)
        if not self.is_logged_in(webpage):
            return self.raise_login_required()

        # Extract access token from webpage
        self._extract_access_token(webpage)
        self._extract_api_gateway(webpage)

        entries = self._fetch_video()

        return {'_type': 'playlist',
                'entries': entries}
