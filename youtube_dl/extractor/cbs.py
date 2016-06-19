from __future__ import unicode_literals

import re

from .theplatform import ThePlatformFeedIE
from ..utils import (
    int_or_none,
    find_xpath_attr,
)


class CBSBaseIE(ThePlatformFeedIE):
    def _parse_smil_subtitles(self, smil, namespace=None, subtitles_lang='en'):
        closed_caption_e = find_xpath_attr(smil, self._xpath_ns('.//param', namespace), 'name', 'ClosedCaptionURL')
        return {
            'en': [{
                'ext': 'ttml',
                'url': closed_caption_e.attrib['value'],
            }]
        } if closed_caption_e is not None and closed_caption_e.attrib.get('value') else []

    def _extract_video_info(self, filter_query, video_id):
        return self._extract_feed_info(
            'dJ5BDC', 'VxxJg8Ymh8sE', filter_query, video_id, lambda entry: {
                'series': entry.get('cbs$SeriesTitle'),
                'season_number': int_or_none(entry.get('cbs$SeasonNumber')),
                'episode': entry.get('cbs$EpisodeTitle'),
                'episode_number': int_or_none(entry.get('cbs$EpisodeNumber')),
            }, {
                'StreamPack': {
                    'manifest': 'm3u',
                }
            })


class CBSIE(CBSBaseIE):
    _VALID_URL = r'(?:cbs:|https?://(?:www\.)?(?:cbs\.com/shows/[^/]+/video|colbertlateshow\.com/(?:video|podcasts))/)(?P<id>[\w-]+)'

    _TESTS = [{
        'url': 'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        'info_dict': {
            'id': '_u7W953k6la293J7EPTd9oHkSPs6Xn6_',
            'display_id': 'connect-chat-feat-garth-brooks',
            'ext': 'mp4',
            'title': 'Connect Chat feat. Garth Brooks',
            'description': 'Connect with country music singer Garth Brooks, as he chats with fans on Wednesday November 27, 2013. Be sure to tune in to Garth Brooks: Live from Las Vegas, Friday November 29, at 9/8c on CBS!',
            'duration': 1495,
            'timestamp': 1385585425,
            'upload_date': '20131127',
            'uploader': 'CBSI-NEW',
        },
        'expected_warnings': ['Failed to download m3u8 information'],
        '_skip': 'Blocked outside the US',
    }, {
        'url': 'http://colbertlateshow.com/video/8GmB0oY0McANFvp2aEffk9jZZZ2YyXxy/the-colbeard/',
        'only_matching': True,
    }, {
        'url': 'http://www.colbertlateshow.com/podcasts/dYSwjqPs_X1tvbV_P2FcPWRa_qT6akTC/in-the-bad-room-with-stephen/',
        'only_matching': True,
    }]
    TP_RELEASE_URL_TEMPLATE = 'http://link.theplatform.com/s/dJ5BDC/%s?mbr=true'

    def _real_extract(self, url):
        content_id = self._match_id(url)
        return self._extract_video_info('byGuid=%s' % content_id, content_id)
