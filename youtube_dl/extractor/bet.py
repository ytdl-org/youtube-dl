from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    xpath_text,
    xpath_with_ns,
    int_or_none,
    parse_iso8601,
)


class BetIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bet\.com/(?:[^/]+/)+(?P<id>.+?)\.html'
    _TESTS = [
        {
            'url': 'http://www.bet.com/news/politics/2014/12/08/in-bet-exclusive-obama-talks-race-and-racism.html',
            'info_dict': {
                'id': 'news/national/2014/a-conversation-with-president-obama',
                'display_id': 'in-bet-exclusive-obama-talks-race-and-racism',
                'ext': 'flv',
                'title': 'A Conversation With President Obama',
                'description': 'md5:699d0652a350cf3e491cd15cc745b5da',
                'duration': 1534,
                'timestamp': 1418075340,
                'upload_date': '20141208',
                'uploader': 'admin',
                'thumbnail': 're:(?i)^https?://.*\.jpg$',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.bet.com/video/news/national/2014/justice-for-ferguson-a-community-reacts.html',
            'info_dict': {
                'id': 'news/national/2014/justice-for-ferguson-a-community-reacts',
                'display_id': 'justice-for-ferguson-a-community-reacts',
                'ext': 'flv',
                'title': 'Justice for Ferguson: A Community Reacts',
                'description': 'A BET News special.',
                'duration': 1696,
                'timestamp': 1416942360,
                'upload_date': '20141125',
                'uploader': 'admin',
                'thumbnail': 're:(?i)^https?://.*\.jpg$',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        }
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        media_url = compat_urllib_parse_unquote(self._search_regex(
            [r'mediaURL\s*:\s*"([^"]+)"', r"var\s+mrssMediaUrl\s*=\s*'([^']+)'"],
            webpage, 'media URL'))

        video_id = self._search_regex(
            r'/video/(.*)/_jcr_content/', media_url, 'video id')

        mrss = self._download_xml(media_url, display_id)

        item = mrss.find('./channel/item')

        NS_MAP = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'media': 'http://search.yahoo.com/mrss/',
            'ka': 'http://kickapps.com/karss',
        }

        title = xpath_text(item, './title', 'title')
        description = xpath_text(
            item, './description', 'description', fatal=False)

        timestamp = parse_iso8601(xpath_text(
            item, xpath_with_ns('./dc:date', NS_MAP),
            'upload date', fatal=False))
        uploader = xpath_text(
            item, xpath_with_ns('./dc:creator', NS_MAP),
            'uploader', fatal=False)

        media_content = item.find(
            xpath_with_ns('./media:content', NS_MAP))
        duration = int_or_none(media_content.get('duration'))
        smil_url = media_content.get('url')

        thumbnail = media_content.find(
            xpath_with_ns('./media:thumbnail', NS_MAP)).get('url')

        formats = self._extract_smil_formats(smil_url, display_id)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'duration': duration,
            'formats': formats,
        }
