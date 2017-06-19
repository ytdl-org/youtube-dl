# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class GlobalNewsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?globalnews\.ca/video/(?P<id>\d+)'
    _TEST = {
        'url': "http://globalnews.ca/video/2066998/focus-montreal-doulia-hamad-and-nebras-m-warsi",
        'info_dict': {
            'title': "Focus Montreal: Doulia Hamad and Nebras M. Warsi",
            'id': '469088323881',
            'ext': 'mp4',
            'upload_date': '20150621',
            'description': 'md5:2998a348701a91ddf70fbb773b016a7f',
            'timestamp': 1434908705,
            'uploader': 'SHWM-NEW',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(
            url,
            display_id
        )

        account_id = self._search_regex((
            r'svp\.platformAccount\s*=\s*(["\']+)(?P<account>.+?)\1',
            r'svp\.(?:videoSMILUrl|metadataUrl)\s*=\s*(["\']+).*?theplatform[^/]+/(?:s|f)/(?P<account>[^/]+?/).*?\1'),
            webpage,
            'account id',
            group='account'
        )[:-1]
        feed_id = self._search_regex((
            r'svp\.feedId\s*=\s*(["\']+)(?P<feed>.+?)\1',
            r'svp\.metadataUrl\s*=\s*(["\']+).*?theplatform[^/]+/f/[^/]+?/(?P<feed>[^?/&#]+).*?\1'),
            webpage,
            'feed id',
            group='feed'
        )
        platform_id = self._search_regex((
            r'<span[^<]+class=(["\'])[^\'"]+?the_platform_id_(?P<platformId>\d+)\1\s+?data-v_count_id=\1\2\1',
            r'svp\.setContentId\(\s*([\'"])(?P<platformId>\d+)\1.*?loadCallback'),
            webpage,
            'platform id',
            group='platformId'
        )

        return {
            'display_id': display_id,
            '_type': 'url_transparent',
            'url': 'http://feed.theplatform.com/f/%s/%s?byId=%s' % (account_id, feed_id, platform_id),
            'ie_key': 'ThePlatformFeed'
        }
