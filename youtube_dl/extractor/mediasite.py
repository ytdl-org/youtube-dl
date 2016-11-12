# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    ExtractorError,
    unsmuggle_url,
    mimetype2ext,
    float_or_none,
)


class MediasiteIE(InfoExtractor):
    _VALID_URL = r'''(?xi)
        https?://[a-z0-9\-\.:\[\]]+/Mediasite/Play/
        (?P<id>[0-9a-f]{32,34})
        (?P<QueryString>\?[^#]+|)
    '''
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
        0: 'video1', # the main video
        2: 'slide',
        3: 'presentation',
        4: 'video2', # screencast?
        5: 'video3',
    }

    def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        mobj = re.match(self._VALID_URL, url)
        ResourceId = mobj.group('id')
        QueryString = mobj.group('QueryString')

        webpage = self._download_webpage(url, ResourceId) # XXX: add UrlReferrer?

        # XXX: might have also extracted UrlReferrer and QueryString from the html
        ServicePath = compat_urlparse.urljoin(url, self._html_search_regex(
            r'<div id="ServicePath">(.+?)</div>', webpage, ResourceId,
            default='/Mediasite/PlayerService/PlayerService.svc/json'))

        PlayerOptions = self._download_json(
            '%s/GetPlayerOptions' % (ServicePath), ResourceId,
            headers={
                'Content-type': 'application/json; charset=utf-8',
                'X-Requested-With': 'XMLHttpRequest',
            },
            data=json.dumps({
                'getPlayerOptionsRequest': {
                    'ResourceId': ResourceId,
                    'QueryString': QueryString,
                    'UrlReferrer': data.get('UrlReferrer', ''),
                    'UseScreenReader': False,
                }
            }).encode('utf-8'))
        Presentation = PlayerOptions['d']['Presentation']
        if Presentation is None:
            raise ExtractorError('Mediasite says: %s' %
                (PlayerOptions['d']['PlayerPresentationStatusMessage'],),
                expected=True)

        thumbnails = []
        formats = []
        for snum, Stream in enumerate(Presentation['Streams']):
            stream_type = self._STREAM_TYPES.get(
                Stream['StreamType'], 'type%u' % Stream['StreamType'])

            stream_formats = []
            for unum, VideoUrl in enumerate(Stream['VideoUrls']):
                url = VideoUrl['Location']
                # XXX: if Stream.get('CanChangeScheme', False), switch scheme to HTTP/HTTPS

                if VideoUrl['MediaType'] == 'SS':
                    stream_formats.extend(self._extract_ism_formats(
                        url, ResourceId, ism_id='%s-%u.%u' % (stream_type, snum, unum)))
                    continue

                stream_formats.append({
                    'format_id': '%s-%u.%u' % (stream_type, snum, unum),
                    'url': url,
                    'ext': mimetype2ext(VideoUrl['MimeType']),
                })

            # TODO: if Stream['HasSlideContent']:
            # synthesise an MJPEG video stream '%s-%u.slides' % (stream_type, snum)
            # from Stream['Slides']
            # this will require writing a custom downloader...

            # disprefer 'secondary' streams
            if Stream['StreamType'] != 0:
                for fmt in stream_formats:
                    fmt['preference'] = -1

            ThumbnailUrl = Stream.get('ThumbnailUrl')
            if ThumbnailUrl:
                thumbnails.append({
                    'id': '%s-%u' % (stream_type, snum),
                    'url': compat_urlparse.urljoin(url, ThumbnailUrl),
                    'preference': -1 if Stream['StreamType'] != 0 else 0,
                })
            formats.extend(stream_formats)

        self._sort_formats(formats)

        # XXX: Presentation['Presenters']
        # XXX: Presentation['Transcript']

        return {
            'id': ResourceId,
            'title': Presentation['Title'],
            'description': Presentation.get('Description'),
            'duration': float_or_none(Presentation.get('Duration'), 1000),
            'timestamp': float_or_none(Presentation.get('UnixTime'), 1000),
            'formats': formats,
            'thumbnails': thumbnails,
        }
