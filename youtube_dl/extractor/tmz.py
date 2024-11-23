# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .jwplatform import JWPlatformIE
from .kaltura import KalturaIE
from ..utils import (
    int_or_none,
    unified_timestamp,
)


class TMZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/videos/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.tmz.com/videos/0-cegprt2p/',
        'md5': '31f9223e20eef55954973359afa61a20',
        'info_dict': {
            'id': 'P6YjLBLk',
            'ext': 'mp4',
            'title': "No Charges Against Hillary Clinton? Harvey Says It Ain't Over Yet",
            'description': 'md5:b714359fc18607715ebccbd2da8ff488',
            'timestamp': 1467831837,
            'upload_date': '20160706',
        },
        'add_ie': [JWPlatformIE.ie_key()],
    }, {
        'url': 'http://www.tmz.com/videos/0_okj015ty/',
        'only_matching': True,
    }, {
        'url': 'https://www.tmz.com/videos/071119-chris-morgan-women-4590005-0-zcsejvcr/',
        'only_matching': True,
    }, {
        'url': 'https://www.tmz.com/videos/2021-02-19-021921-floyd-mayweather-1043872/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url).replace('-', '_')

        webpage = self._download_webpage(url, video_id, fatal=False)
        if webpage:
            tmz_video_id = self._search_regex(
                r'nodeRef\s*:\s*["\']tmz:video:([\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12})',
                webpage, 'video id', default=None)
            video = self._download_json(
                'https://www.tmz.com/_/video/%s' % tmz_video_id, video_id,
                fatal=False)
            if video:
                message = video['message']
                info = {
                    '_type': 'url_transparent',
                    'title': message.get('title'),
                    'description': message.get('description'),
                    'timestamp': unified_timestamp(message.get('published_at')),
                    'duration': int_or_none(message.get('duration')),
                }
                jwplatform_id = message.get('jwplayer_media_id')
                if jwplatform_id:
                    info.update({
                        'url': 'jwplatform:%s' % jwplatform_id,
                        'ie_key': JWPlatformIE.ie_key(),
                    })
                else:
                    kaltura_entry_id = message.get('kaltura_entry_id') or video_id
                    kaltura_partner_id = message.get('kaltura_partner_id') or '591531'
                    info.update({
                        'url': 'kaltura:%s:%s' % (kaltura_partner_id, kaltura_entry_id),
                        'ie_key': KalturaIE.ie_key(),
                    })
                return info

        return self.url_result(
            'kaltura:591531:%s' % video_id, KalturaIE.ie_key(), video_id)


class TMZArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/\d{4}/\d{2}/\d{2}/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://www.tmz.com/2015/04/19/bobby-brown-bobbi-kristina-awake-video-concert',
        'info_dict': {
            'id': 'PAKZa97W',
            'ext': 'mp4',
            'title': 'Bobby Brown Tells Crowd ... Bobbi Kristina is Awake',
            'description': 'Bobby Brown stunned his audience during a concert Saturday night, when he told the crowd, "Bobbi is awake.  She\'s watching me."',
            'timestamp': 1429466400,
            'upload_date': '20150419',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': [JWPlatformIE.ie_key()],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        tmz_url = self._search_regex(
            r'clickLink\s*\(\s*["\'](?P<url>%s)' % TMZIE._VALID_URL, webpage,
            'video id', default=None, group='url')
        if tmz_url:
            return self.url_result(tmz_url, ie=TMZIE.ie_key())

        embedded_video_info = self._parse_json(self._html_search_regex(
            r'tmzVideoEmbed\(({.+?})\);', webpage, 'embedded video info'),
            video_id)
        return self.url_result(
            'http://www.tmz.com/videos/%s/' % embedded_video_info['id'],
            ie=TMZIE.ie_key())
