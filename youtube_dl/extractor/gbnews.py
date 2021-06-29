# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
)
from ..utils import (
    extract_attributes,
    ExtractorError,
    try_get,
)


class GBNewsIE(InfoExtractor):
    '''GB News clips and features'''

    _VALID_URL = r'https?://(?:www\.)?gbnews\.uk/(?:shows(?:/(?P<display_id>[^/]+))?|a)/(?P<id>\d+)'
    _PLATFORM = 'safari'
    _SSMP_URL = 'https://mm-dev.simplestream.com/ssmp/api.php'
    _TESTS = [{
        'url': 'https://www.gbnews.uk/shows/andrew-neils-message-to-companies-choosing-to-boycott-gb-news/106889',
        'info_dict': {
            'id': '106889',
            'ext': 'mp4',
            'title': "Andrew Neil's message to companies choosing to boycott GB News",
            'description': 'md5:b281f5d22fd6d5eda64a4e3ba771b351',
        },
    },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)
        # extraction based on https://github.com/ytdl-org/youtube-dl/issues/29341
        '''
        <div id="video-106908"
            class="simplestream"
            data-id="GB001"
            data-type="vod"
            data-key="3Li3Nt2Qs8Ct3Xq9Fi5Uy0Mb2Bj0Qs"
            data-token="f9c317c727dc07f515b20036c8ef14a6"
            data-expiry="1624300052"
            data-uvid="37900558"
            data-poster="https://thumbnails.simplestreamcdn.com/gbnews/ondemand/37900558.jpg?width=700&"
            data-npaw="false"
            data-env="production">
        '''
        # exception if no match
        video_data = self._search_regex(
            r'<\s*div\s[^>]*class\s*=\s*([\'"])simplestream\1[^>]*>',
            webpage, "video data", group=0)

        # print(video_data)
        video_data = extract_attributes(video_data)
        ss_id = try_get(video_data, lambda x: x['data-id'])
        if not ss_id:
            raise ExtractorError('Simplestream ID not found')

        # exception if no JSON
        json_data = self._download_json(
            self._SSMP_URL, display_id,
            note='Downloading Simplestream JSON metadata',
            errnote='Unable to download Simplestream JSON metadata',
            query={
                'id': ss_id,
                'env': video_data.get('data-env'),
            })

        meta_url = try_get(json_data, lambda x: x['response']['api_hostname'], compat_str)
        if not meta_url:
            raise ExtractorError('No API host found')

        uvid = video_data.get('data-uvid')
        dtype = video_data.get('data-type')
        # exception if no JSON
        stream_data = self._download_json(
            '%s/api/%s/stream/%s' % (meta_url, 'show' if dtype == 'vod' else dtype, uvid),
            display_id,
            query={
                'key': video_data.get('data-key'),
                'platform': self._PLATFORM,
            },
            headers={
                'Token': video_data.get('data-token'),
                'Token-Expiry': video_data.get('data-expiry'),
                'Uvid': uvid,
            })

        stream_url = try_get(stream_data, lambda x: x['response']['stream'], compat_str)
        if not stream_url:
            raise ExtractorError('No stream data')

        # now known to be a dict
        stream_data = stream_data['response']
        drm = stream_data.get('drm')
        if drm:
            raise ExtractorError(
                'Stream is requesting DRM (%s) playback: unsupported' % drm,
                expected=True)

        formats = []
        formats.extend(
            self._extract_m3u8_formats(stream_url, display_id, ext='mp4', fatal=False))

        # exception if no formats
        self._sort_formats(formats)

        # no 'title' attribute seen, but if it comes ...
        title = stream_data.get('title') or self._og_search_title(webpage)

        return {
            'id': display_id,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': video_data.get('data-poster') or None,
            'formats': formats,
            'is_live': 'Live' in self.IE_NAME,
        }


class GBNewsLiveIE(GBNewsIE):
    '''GB News live programme stream'''

    _VALID_URL = r'https?://(?:www.)?gbnews.uk/(?P<id>watchlive)(?:$|[/?#])'
    _TESTS = [{
        'url': 'https://www.gbnews.uk/watchlive',
        'info_dict': {
            'id': 'watchlive',
            'ext': 'mp4',
            'title': "Watchlive",
            'is_live': True,
        },
    },
    ]

    '''
    <div id="video-104872"
        class="simplestream"
        data-id="gb002"
        data-type="live"
        data-key="3Li3Nt2Qs8Ct3Xq9Fi5Uy0Mb2Bj0Qs"
        data-token="d10b3ea37f6ce539ffd1ce2f6ce5fe35"
        data-expiry="1624984755"
        data-uvid="1069"
        data-poster=""
        data-npaw="false"
        data-env="production">
    </div>
    '''
