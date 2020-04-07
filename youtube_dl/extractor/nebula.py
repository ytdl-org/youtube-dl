# coding: utf-8
from __future__ import unicode_literals

import os

from .common import InfoExtractor
from ..utils import parse_iso8601

COOKIE_NEBULA_AUTH = os.environ.get('COOKIE_NEBULA_AUTH')   # FIXME: a workaround for testing, because I couldn't figure out how to supply a cookiejar when running the unit tests


class NebulaIE(InfoExtractor):
    """
    Nebula (https://watchnebula.com/) is a video platform created by the streamer community Standard. It hosts videos
    off-YouTube from a small hand-picked group of creators.

    All videos require a subscription to watch. There are no known freely available videos. So the test case is
    disabled (but should pass when supplying a 'nebula-auth' cookie for an account with a valid subscription).

    Nebula uses the Zype video infrastructure and this extractor is using the 'url_transparent' mode to hand off
    video extraction to the Zype extractor.

    This description has been last updated on 2020-04-07.
    """

    _VALID_URL = r'https?://(?:www\.)?watchnebula\.com/videos/(?P<id>[-\w]+)'   # the 'id' group is actually the slug, but we misname it 'id' to be able to use _match_id()
    _TEST = {
        'url': 'https://watchnebula.com/videos/that-time-disney-remade-beauty-and-the-beast',
        'md5': 'fe79c4df8b3aa2fea98a93d027465c7e',
        'info_dict': {
            'id': '5c271b40b13fd613090034fd',
            'ext': 'mp4',
            'title': 'That Time Disney Remade Beauty and the Beast',
            'description': 'Note: this video was originally posted on YouTube with the sponsor read included. We weren’t able to remove it without reducing video quality, so it’s presented here in its original context.',
            'upload_date': '20180731',
            'timestamp': 1533009600,
            #'uploader': 'Lindsay Ellis',   # TODO: removed because unreliable/sometimes incorrect
        }
    }
    _WORKING = False   # this is set to False because the test won't pass without an auth cookie for a (paid) subscription

    def _extract_state_object(self, webpage, display_id):
        """
        As of 2020-04-07, every Nebula video page is a React base page, containing an initial state JSON in a script
        tag. This function is extracting this script tag, parsing it as JSON.
        """
        initial_state_object = self._search_regex(r'<script id="initial-app-state" type="application/json">(.+?)</script>', webpage, 'initial_state')
        metadata = self._parse_json(initial_state_object, video_id=display_id)   # TODO: we don't have the real video ID yet, is it okay to pass the display_id instead?

        return metadata

    def _extract_video_metadata(self, state_object, display_id):
        """
        The state object contains a videos.byURL dictionary, which maps URL display IDs to video IDs. Using the
        video ID, we can then extract a dictionary with various meta data about the video itself.
        """
        video_id = state_object['videos']['byURL'][display_id]
        video_meta = state_object['videos']['byID'][video_id]

        return video_id, video_meta

    def _extract_video_url(self, webpage, state_object, video_id):
        """
        To get the embed URL of the actual video stream, we could reconstruct it from the video ID, but it seems a
        bit more stable to extract the iframe source that links to the video.
        """
        iframe = self._search_regex(r'<iframe(.+?)</iframe>', webpage, 'iframe', fatal=False)
        video_url = self._search_regex(r'src="(.+?)"', iframe, 'iframe-src', fatal=False) if iframe else None

        # fallback: reconstruct using video ID and access token from state object
        if not video_url:
            access_token = state_object['account']['userInfo']['zypeAuthInfo']['accessToken']
            video_url = 'https://player.zype.com/embed/{video_id}.html?access_token={access_token}'.format(video_id=video_id, access_token=access_token)

        return video_url

    def _extract_uploader(self, video_meta):
        """
        Nebula doesn't really seem to have the concept of an uploader internally, videos are often organized
        more like a (TV) series than by uploader. But in the example case, Lindsay Ellis is the creator, so
        I'll go with this for now.
        """
        return video_meta['categories'][0]['value'][0]

    def _real_extract(self, url):
        # FIXME: a workaround for testing, because I couldn't figure out how to supply a cookiejar when running the unit tests
        if COOKIE_NEBULA_AUTH:
            self._set_cookie('watchnebula.com', 'nebula-auth', COOKIE_NEBULA_AUTH)

        # extract the video's display ID from the URL (we'll retrieve the video ID later)
        display_id = self._match_id(url)

        # download the page
        webpage = self._download_webpage(url, video_id=display_id)    # TODO: what video ID do I supply, as I don't know it yet? _download_webpage doesn't accept a display_id instead...

        # extract the state object from the webpage, and then retrieve video meta data from it
        state_object = self._extract_state_object(webpage, display_id)
        video_id, video_meta = self._extract_video_metadata(state_object, display_id)

        # extract the video URL from the webpage
        video_url = self._extract_video_url(webpage, state_object, video_id)

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
            'title': video_meta['title'],
            'description': video_meta['description'],
            'timestamp': parse_iso8601(video_meta['published_at']),
            #'uploader': self._extract_uploader(video_meta),   # TODO: removed because unreliable/sometimes incorrect
            'thumbnails': [
                {
                    'id': tn['name'],   # this appears to be null in all cases I've seen
                    'url': tn['url'],
                    'width': tn['width'],
                    'height': tn['height'],
                } for tn in video_meta['thumbnails']
            ],
            'duration': video_meta['duration'],
            # TODO: uploader_url: the video page clearly links to this (in the example case: /lindsayellis), but I cannot figure out where it gets it from!
            # TODO: channel
            # TODO: channel_id
            # TODO: channel_url
        }
