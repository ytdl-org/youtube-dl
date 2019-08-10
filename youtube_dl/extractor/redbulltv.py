# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import RegexNotFoundError
import json
import time


class RedBullTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redbull\.com/[^/]+/(?:videos|recap-videos|events|episodes|films)/(?P<id>AP-\w+)'
    _TESTS = [{
        # film
        'url': 'https://www.redbull.tv/video/AP-1Q6XCDTAN1W11',
        'md5': 'fb0445b98aa4394e504b413d98031d1f',
        'info_dict': {
            'id': 'AP-1Q6XCDTAN1W11',
            'ext': 'mp4',
            'title': 'ABC of... WRC - ABC of... S1E6',
            'description': 'md5:5c7ed8f4015c8492ecf64b6ab31e7d31',
            'duration': 1582.04,
        },
    }, {
        # episode
        'url': 'https://www.redbull.tv/video/AP-1PMHKJFCW1W11',
        'info_dict': {
            'id': 'AP-1PMHKJFCW1W11',
            'ext': 'mp4',
            'title': 'Grime - Hashtags S2E4',
            'description': 'md5:b5f522b89b72e1e23216e5018810bb25',
            'duration': 904.6,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.redbull.com/int-en/tv/video/AP-1UWHCAR9S1W11/rob-meets-sam-gaze?playlist=playlists::3f81040a-2f31-4832-8e2e-545b1d39d173',
        'only_matching': True,
    }, {
        'url': 'https://www.redbull.com/us-en/videos/AP-1YM9QCYE52111',
        'only_matching': True,
    }, {
        'url': 'https://www.redbull.com/us-en/events/AP-1XV2K61Q51W11/live/AP-1XUJ86FDH1W11',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        # video_id is "AP-..." ID
        video_id = self._match_id(url)

        # Try downloading the webpage multiple times in order to get a repsonse
        # cache which will contain the result of a query to 
        # 'https://www.redbull.com/v3/api/composition/v3/query/en-INT?rb3Schema=v1:pageConfig&filter[uriSlug]=%s' % video_id
        # We use the response cache to get the rrn ID and other metadata. We do
        # this instead of simply querying the API in order to preserve the
        # provided URL's locale. (Annoyingly, the locale in the input URL 
        # ('en-us', for example) is of a different format than the locale
        # required for the API request.)
        tries = 3
        for i in range(tries):
            try:
                if i == 0:
                    webpage = self._download_webpage(url, video_id)
                else:
                    webpage = self._download_webpage(url, video_id, note='Redownloading webpage')
                # extract response cache
                response_cache = json.loads(self._html_search_regex(r'<script type="application/json" id="response-cache">(.+?)</script>', webpage, 'response-cache'))
                break
            except RegexNotFoundError:
                if i < tries - 1:
                    self.to_screen('Waiting before redownloading webpage')
                    time.sleep(2)
                else:
                    raise

        # select the key that includes the string 'pageConfig'
        metadata = json.loads(
                response_cache[
                    [key for key in response_cache.keys() if 'pageConfig' in key][0]
                ]['response']
            )['data']

        # extract rrn ID
        rrn_id_ext = metadata['analytics']['asset']['trackingDimensions']['masterID']
        # trim locale from the end of rrn_id_ext
        rrn_id = ':'.join(rrn_id_ext.split(':')[:-1])

        # extract metadata
        title = metadata['analytics']['asset']['title']
        short_description = metadata['pageMeta']['og:title']
        long_description = metadata['pageMeta']['og:description']

        # get access token for download
        session = self._download_json(
            'https://api.redbull.tv/v3/session', video_id,
            note='Downloading access token', query={
                'category': 'personal_computer',
                'os_family': 'http',
            })
        if session.get('code') == 'error':
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, session['message']))
        token = session['token']

        formats = self._extract_m3u8_formats(
            'https://dms.redbull.tv/v3/%s/%s/playlist.m3u8' % (rrn_id, token),
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': long_description or short_description,
            'formats': formats,
        }
