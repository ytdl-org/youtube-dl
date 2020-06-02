# coding: utf-8
from __future__ import unicode_literals

import os

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote, compat_str
from ..utils import parse_iso8601, ExtractorError, try_get, urljoin


class NebulaIE(InfoExtractor):
    """
    Nebula (https://watchnebula.com/) is a video platform created by the streamer community Standard. It hosts videos
    off-YouTube from a small hand-picked group of creators.

    All videos require a subscription to watch. There are no known freely available videos. An authentication token to
    an account with a valid subscription can be specified in multiple ways.

    Nebula uses the Zype video infrastructure and this extractor is using the 'url_transparent' mode to hand off
    video extraction to the Zype extractor.

    This description has been last updated on 2020-05-11.
    """

    _VALID_URL = r'https?://(?:www\.)?watchnebula\.com/videos/(?P<id>[-\w]+)'   # the 'id' group is actually the display_id, but we misname it 'id' to be able to use _match_id()
    _TESTS = [
        {
            'url': 'https://watchnebula.com/videos/that-time-disney-remade-beauty-and-the-beast',
            'md5': 'fe79c4df8b3aa2fea98a93d027465c7e',
            'info_dict': {
                'id': '5c271b40b13fd613090034fd',
                'ext': 'mp4',
                'title': 'That Time Disney Remade Beauty and the Beast',
                'description': 'Note: this video was originally posted on YouTube with the sponsor read included. We weren’t able to remove it without reducing video quality, so it’s presented here in its original context.',
                'upload_date': '20180731',
                'timestamp': 1533009600,
                'channel': 'Lindsay Ellis',
                'uploader': 'Lindsay Ellis',
            }
        },
        {
            'url': 'https://watchnebula.com/videos/the-logistics-of-d-day-landing-craft-how-the-allies-got-ashore',
            'md5': 'b0b171504d67e2822179149ccd6787db',
            'info_dict': {
                'id': '5e7e78171aaf320001fbd6be',
                'ext': 'mp4',
                'title': 'Landing Craft - How The Allies Got Ashore',
                'description': r're:^In this episode we explore the unsung heroes of D-Day, the landing craft.',
                'upload_date': '20200327',
                'timestamp': 1585348140,
                'channel': 'The Logistics of D-Day',
                'uploader': 'The Logistics of D-Day',
            }
        },
        {
            'url': 'https://watchnebula.com/videos/money-episode-1-the-draw',
            'md5': '98e96346caa3b303fec4493c5d49dcb5',
            'info_dict': {
                'id': '5e779ebdd157bc0001d1c75a',
                'ext': 'mp4',
                'title': 'Episode 1: The Draw',
                'description': r'contains:There’s free money on offer… if the players can all work together.',
                'upload_date': '20200323',
                'timestamp': 1584980400,
                'channel': 'Tom Scott Presents: Money',
                'uploader': 'Tom Scott Presents: Money',
            }
        },
    ]
    _WORKING = True   # FIXME: should this be set to False, to hide the tests from CI, given that the unit tests require an auth cookie of a (paid) subscription?

    def _retrieve_nebula_auth(self, video_id):
        """
        Attempt to find a Nebula API token. Makes multiple attempts in the following order:
        a) the --video-password command line argument
        b) the --cookies supplied cookie jar
        c) the NEBULA_TOKEN environment variable
        If none of these are successful, an end user-intended error message is returned, listing some solutions.

        # TODO: are these authentication methods, in this order, the best practice for youtube-dl?
        """
        nebula_token = self._downloader.params.get('videopassword')
        if not nebula_token:
            # TODO: is there a helper to do all this cookie extraction?
            nebula_cookies = self._get_cookies('https://watchnebula.com')
            nebula_cookie = nebula_cookies.get('nebula-auth')
            if nebula_cookie:
                nebula_cookie_value = compat_urllib_parse_unquote(nebula_cookie.value)
                nebula_token = self._parse_json(nebula_cookie_value, video_id).get('apiToken')
        if not nebula_token and 'NEBULA_TOKEN' in os.environ:
            nebula_token = os.environ.get('NEBULA_TOKEN')
        if not nebula_token:
            raise ExtractorError('Nebula requires an account with an active subscription. '
                                 'You can supply a corresponding token by either '
                                 'a) finding your nebula-auth cookie and then specifying it via --video-password, or '
                                 'b) passing in a cookie jar containing a nebula-auth cookie via --cookies, or '
                                 'c) setting the environment variable NEBULA_TOKEN.')
        return nebula_token

    def _retrieve_zype_api_key(self, page_url, display_id):
        """
        Retrieves the Zype API key required to make calls to the Zype API.

        Unfortunately, the Nebula frontend stores this as a JS object literal in one of its JS chunks,
        looking somewhat like this (but minified):

            return {
                NODE_ENV: "production",
                REACT_APP_NAME: "Nebula",
                REACT_APP_NEBULA_API: "https://api.watchnebula.com/api/v1/",
                REACT_APP_ZYPE_API: "https://api.zype.com/",
                REACT_APP_ZYPE_API_KEY: "<redacted>",
                REACT_APP_ZYPE_APP_KEY: "<redacted>",
                // ...
            }

        So we have to find the reference to the chunk in the video page (as it is hashed and the hash will
        change when they do a new release), then download the chunk and extract the API key from there,
        hoping they won't rename the constant.

        Alternatively, it is currently hardcoded and shared among all users. We haven't seen it
        change so far, so we could also just hardcode it in the extractor as a fallback.
        """
        # fetch the video page
        webpage = self._download_webpage(page_url, video_id=display_id)

        # find the script tag with a file named 'main.<hash>.chunk.js' in there
        main_script_relpath = self._search_regex(
            r'<script[^>]*src="(?P<script_relpath>[^"]*main.[0-9a-f]*.chunk.js)"[^>]*>', webpage,
            group='script_relpath', name='script relative path', fatal=True)

        # fetch the JS chunk
        main_script_abspath = urljoin(page_url, main_script_relpath)
        main_script = self._download_webpage(main_script_abspath, video_id=display_id,
                                             note='Retrieving Zype API key')

        # find the API key named 'REACT_APP_ZYPE_API_KEY' in there
        api_key = self._search_regex(
            r'REACT_APP_ZYPE_API_KEY\s*:\s*"(?P<api_key>[\w-]*)"', main_script,
            group='api_key', name='API key', fatal=True)

        return api_key

    def _call_zype_api(self, path, params, video_id, api_key, note):
        """
        A helper for making calls to the Zype API.
        """
        query = {'api_key': api_key, 'per_page': 1}
        query.update(params)
        return self._download_json('https://api.zype.com' + path, video_id, query=query, note=note)

    def _fetch_zype_video_data(self, display_id, api_key):
        """
        Fetch video meta data from the Zype API.
        """
        response = self._call_zype_api('/videos', {'friendly_title': display_id},
                                       display_id, api_key, note='Retrieving metadata from Zype')
        if 'response' not in response or len(response['response']) != 1:
            raise ExtractorError('Unable to find video on Zype API')
        return response['response'][0]

    def _call_nebula_api(self, path, video_id, access_token, note):
        """
        A helper for making calls to the Nebula API.
        """
        return self._download_json('https://api.watchnebula.com/api/v1' + path, video_id, headers={
            'Authorization': 'Token {access_token}'.format(access_token=access_token)
        }, note=note)

    def _fetch_zype_access_token(self, video_id, nebula_token):
        """
        Requests a Zype access token from the Nebula API.
        """
        user_object = self._call_nebula_api('/auth/user/', video_id, nebula_token, note='Retrieving Zype access token')
        access_token = try_get(user_object, lambda x: x['zype_auth_info']['access_token'], compat_str)
        if not access_token:
            raise ExtractorError('Unable to extract Zype access token from Nebula API authentication endpoint')
        return access_token

    def _build_video_url(self, video_id, zype_access_token):
        """
        Construct a Zype video URL (as supported by the Zype extractor), given a Zype video ID and a Zype access token.
        """
        return 'https://player.zype.com/embed/{video_id}.html?access_token={access_token}'.format(
            video_id=video_id,
            access_token=zype_access_token)

    def _extract_channel(self, video_meta):
        """
        Extract the channel title, by going through the list of categories and finding the first value of the
        first category that has a value.

        I know this look like a terrible approach. But actually, it's just reproducing the behavior of the
        React code the Nebula frontend uses (as of 2020-04-07):

            let channel;
            if (video && video.categories && video.categories.length) {
                const channelTitle = video.categories.map((category) => (category.value[0]))
                                                     .filter((title) => (!!title))[0];
                channel = getChannelByTitle(state, { title: channelTitle });
            }

        Basically, it finds the first (truthy) value in the category list and that's assumed to be the
        channel title. And then the channel details (e.g. the URL) are looked up by title (!) (not by any
        kind of ID) via an additional API call.

        TODO: Implement the API calls giving us the channel list, so that we can do the title lookup and then figure out the channel URL

        May return None of no category list could be found or no category had a label ('value').
        """
        categories = video_meta.get('categories', []) if video_meta else []
        for category in categories:
            if category.get('value'):   # we're intentionally not using "'value' in category" here, because the expression is supposed to be falsy for empty lists in category['value'] as well!
                return category['value'][0]

    def _real_extract(self, url):
        # extract the video's display ID from the URL (we'll retrieve the video ID later)
        display_id = self._match_id(url)

        # retrieve Nebula authentication information
        nebula_token = self._retrieve_nebula_auth(display_id)

        # fetch video meta data from the Nebula API
        api_key = self._retrieve_zype_api_key(url, display_id)
        video_meta = self._fetch_zype_video_data(display_id, api_key)
        video_id = video_meta['_id']

        # extract additional info
        channel_title = self._extract_channel(video_meta)

        # fetch the access token for Zype, then construct the video URL
        zype_access_token = self._fetch_zype_access_token(display_id, nebula_token=nebula_token)
        video_url = self._build_video_url(video_id, zype_access_token)

        return {
            'id': video_id,
            'display_id': display_id,

            # we're passing this video URL on to the 'Zype' extractor (that's the video infrastructure that Nebula is
            # built on top of) and use the 'url_transparent' type to indicate that our meta data should be better than
            # whatever the Zype extractor is able to identify
            '_type': 'url_transparent',
            'ie_key': 'Zype',
            'url': video_url,

            # the meta data we were able to extract from Nebula
            'title': video_meta.get('title'),
            'description': video_meta.get('description'),
            'timestamp': parse_iso8601(video_meta.get('published_at')),
            'thumbnails': [
                {
                    'id': tn.get('name'),   # this appears to be null in all cases I've encountered
                    'url': tn['url'],
                    'width': tn.get('width'),
                    'height': tn.get('height'),
                } for tn in video_meta.get('thumbnails', [])],
            'duration': video_meta.get('duration'),
            'channel': channel_title,
            'uploader': channel_title,   # we chose here to declare the channel name as the 'uploader' -- that's certainly arguable, as sometimes it's more of a series
            # TODO: uploader_url: the video page clearly links to this (in the example case: /lindsayellis), but I cannot figure out where it gets it from!
            # TODO: channel_id
            # TODO: channel_url
        }
