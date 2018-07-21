# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    mimetype2ext,
    unescapeHTML,
    unsmuggle_url,
    url_or_none,
    urljoin,
)


class MediasiteIE(InfoExtractor):
    _VALID_URL = r'(?xi)https?://[^/]+/Mediasite/Play/(?P<id>[0-9a-f]{32,34})(?P<query>\?[^#]+|)'
    _TESTS = [
        {
            'url': 'https://hitsmediaweb.h-its.org/mediasite/Play/2db6c271681e4f199af3c60d1f82869b1d',
            'info_dict': {
                'id': '2db6c271681e4f199af3c60d1f82869b1d',
                'ext': 'mp4',
                'title': 'Lecture: Tuesday, September 20, 2016 - Sir Andrew Wiles',
                'description': 'Sir Andrew Wiles: “Equations in arithmetic”\\n\\nI will describe some of the interactions between modern number theory and the problem of solving equations in rational numbers or integers\\u0027.',
                'timestamp': 1474268400.0,
                'upload_date': '20160919',
            },
        },
        {
            'url': 'http://mediasite.uib.no/Mediasite/Play/90bb363295d945d6b548c867d01181361d?catalog=a452b7df-9ae1-46b7-a3ba-aceeb285f3eb',
            'info_dict': {
                'id': '90bb363295d945d6b548c867d01181361d',
                'ext': 'mp4',
                'upload_date': '20150429',
                'title': '5) IT-forum 2015-Dag 1  - Dungbeetle -  How and why Rain created a tiny bug tracker for Unity',
                'timestamp': 1430311380.0,
            },
        },
        {
            'url': 'https://collegerama.tudelft.nl/Mediasite/Play/585a43626e544bdd97aeb71a0ec907a01d',
            'md5': '481fda1c11f67588c0d9d8fbdced4e39',
            'info_dict': {
                'id': '585a43626e544bdd97aeb71a0ec907a01d',
                'ext': 'mp4',
                'title': 'Een nieuwe wereld: waarden, bewustzijn en techniek van de mensheid 2.0.',
                'description': '',
                'thumbnail': r're:^https?://.*\.jpg(?:\?.*)?$',
                'duration': 7713.088,
                'timestamp': 1413309600,
                'upload_date': '20141014',
            },
        },
        {
            'url': 'https://collegerama.tudelft.nl/Mediasite/Play/86a9ea9f53e149079fbdb4202b521ed21d?catalog=fd32fd35-6c99-466c-89d4-cd3c431bc8a4',
            'md5': 'ef1fdded95bdf19b12c5999949419c92',
            'info_dict': {
                'id': '86a9ea9f53e149079fbdb4202b521ed21d',
                'ext': 'wmv',
                'title': '64ste Vakantiecursus: Afvalwater',
                'description': 'md5:7fd774865cc69d972f542b157c328305',
                'thumbnail': r're:^https?://.*\.jpg(?:\?.*?)?$',
                'duration': 10853,
                'timestamp': 1326446400,
                'upload_date': '20120113',
            },
        },
        {
            'url': 'http://digitalops.sandia.gov/Mediasite/Play/24aace4429fc450fb5b38cdbf424a66e1d',
            'md5': '9422edc9b9a60151727e4b6d8bef393d',
            'info_dict': {
                'id': '24aace4429fc450fb5b38cdbf424a66e1d',
                'ext': 'mp4',
                'title': 'Xyce Software Training - Section 1',
                'description': r're:(?s)SAND Number: SAND 2013-7800.{200,}',
                'upload_date': '20120409',
                'timestamp': 1333983600,
                'duration': 7794,
            }
        }
    ]

    # look in Mediasite.Core.js (Mediasite.ContentStreamType[*])
    _STREAM_TYPES = {
        0: 'video1',  # the main video
        2: 'slide',
        3: 'presentation',
        4: 'video2',  # screencast?
        5: 'video3',
    }

    @staticmethod
    def _extract_urls(webpage):
        return [
            unescapeHTML(mobj.group('url'))
            for mobj in re.finditer(
                r'(?xi)<iframe\b[^>]+\bsrc=(["\'])(?P<url>(?:(?:https?:)?//[^/]+)?/Mediasite/Play/[0-9a-f]{32,34}(?:\?.*?)?)\1',
                webpage)]

    def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        mobj = re.match(self._VALID_URL, url)
        resource_id = mobj.group('id')
        query = mobj.group('query')

        webpage, urlh = self._download_webpage_handle(url, resource_id)  # XXX: add UrlReferrer?
        redirect_url = compat_str(urlh.geturl())

        # XXX: might have also extracted UrlReferrer and QueryString from the html
        service_path = compat_urlparse.urljoin(redirect_url, self._html_search_regex(
            r'<div[^>]+\bid=["\']ServicePath[^>]+>(.+?)</div>', webpage, resource_id,
            default='/Mediasite/PlayerService/PlayerService.svc/json'))

        player_options = self._download_json(
            '%s/GetPlayerOptions' % service_path, resource_id,
            headers={
                'Content-type': 'application/json; charset=utf-8',
                'X-Requested-With': 'XMLHttpRequest',
            },
            data=json.dumps({
                'getPlayerOptionsRequest': {
                    'ResourceId': resource_id,
                    'QueryString': query,
                    'UrlReferrer': data.get('UrlReferrer', ''),
                    'UseScreenReader': False,
                }
            }).encode('utf-8'))['d']

        presentation = player_options['Presentation']
        title = presentation['Title']

        if presentation is None:
            raise ExtractorError(
                'Mediasite says: %s' % player_options['PlayerPresentationStatusMessage'],
                expected=True)

        thumbnails = []
        formats = []
        for snum, Stream in enumerate(presentation['Streams']):
            stream_type = Stream.get('StreamType')
            if stream_type is None:
                continue

            video_urls = Stream.get('VideoUrls')
            if not isinstance(video_urls, list):
                video_urls = []

            stream_id = self._STREAM_TYPES.get(
                stream_type, 'type%u' % stream_type)

            stream_formats = []
            for unum, VideoUrl in enumerate(video_urls):
                video_url = url_or_none(VideoUrl.get('Location'))
                if not video_url:
                    continue
                # XXX: if Stream.get('CanChangeScheme', False), switch scheme to HTTP/HTTPS

                media_type = VideoUrl.get('MediaType')
                if media_type == 'SS':
                    stream_formats.extend(self._extract_ism_formats(
                        video_url, resource_id,
                        ism_id='%s-%u.%u' % (stream_id, snum, unum),
                        fatal=False))
                elif media_type == 'Dash':
                    stream_formats.extend(self._extract_mpd_formats(
                        video_url, resource_id,
                        mpd_id='%s-%u.%u' % (stream_id, snum, unum),
                        fatal=False))
                else:
                    stream_formats.append({
                        'format_id': '%s-%u.%u' % (stream_id, snum, unum),
                        'url': video_url,
                        'ext': mimetype2ext(VideoUrl.get('MimeType')),
                    })

            # TODO: if Stream['HasSlideContent']:
            # synthesise an MJPEG video stream '%s-%u.slides' % (stream_type, snum)
            # from Stream['Slides']
            # this will require writing a custom downloader...

            # disprefer 'secondary' streams
            if stream_type != 0:
                for fmt in stream_formats:
                    fmt['preference'] = -1

            thumbnail_url = Stream.get('ThumbnailUrl')
            if thumbnail_url:
                thumbnails.append({
                    'id': '%s-%u' % (stream_id, snum),
                    'url': urljoin(redirect_url, thumbnail_url),
                    'preference': -1 if stream_type != 0 else 0,
                })
            formats.extend(stream_formats)

        self._sort_formats(formats)

        # XXX: Presentation['Presenters']
        # XXX: Presentation['Transcript']

        return {
            'id': resource_id,
            'title': title,
            'description': presentation.get('Description'),
            'duration': float_or_none(presentation.get('Duration'), 1000),
            'timestamp': float_or_none(presentation.get('UnixTime'), 1000),
            'formats': formats,
            'thumbnails': thumbnails,
        }
