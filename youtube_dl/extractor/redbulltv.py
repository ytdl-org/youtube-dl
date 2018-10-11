# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    float_or_none,
    ExtractorError,
)


class RedBullTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redbull(?:\.tv|\.com/(?:[^/]+/)?tv)/video/(?P<id>AP-\w+)'
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
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

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

        try:
            video = self._download_json(
                'https://api.redbull.tv/v3/products/' + video_id,
                video_id, note='Downloading video information',
                headers={'Authorization': token}
            )
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                error_message = self._parse_json(
                    e.cause.read().decode(), video_id)['error']
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error_message), expected=True)
            raise

        title = video['title'].strip()

        formats = self._extract_m3u8_formats(
            'https://dms.redbull.tv/v3/%s/%s/playlist.m3u8' % (video_id, token),
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        subtitles = {}
        for resource in video.get('resources', []):
            if resource.startswith('closed_caption_'):
                splitted_resource = resource.split('_')
                if splitted_resource[2]:
                    subtitles.setdefault('en', []).append({
                        'url': 'https://resources.redbull.tv/%s/%s' % (video_id, resource),
                        'ext': splitted_resource[2],
                    })

        subheading = video.get('subheading')
        if subheading:
            title += ' - %s' % subheading

        return {
            'id': video_id,
            'title': title,
            'description': video.get('long_description') or video.get(
                'short_description'),
            'duration': float_or_none(video.get('duration'), scale=1000),
            'formats': formats,
            'subtitles': subtitles,
        }
