# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
    xpath_with_ns,
    xpath_text,
    find_xpath_attr,
)


class AftenpostenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?aftenposten\.no/webtv/([^/]+/)*(?P<id>[^/]+)-\d+\.html'

    _TEST = {
        'url': 'http://www.aftenposten.no/webtv/serier-og-programmer/sweatshopenglish/TRAILER-SWEATSHOP---I-cant-take-any-more-7800835.html?paging=&section=webtv_serierogprogrammer_sweatshop_sweatshopenglish',
        'md5': 'fd828cd29774a729bf4d4425fe192972',
        'info_dict': {
            'id': '21039',
            'ext': 'mov',
            'title': 'TRAILER: "Sweatshop" - I can´t take any more',
            'description': 'md5:21891f2b0dd7ec2f78d84a50e54f8238',
            'timestamp': 1416927969,
            'upload_date': '20141125',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_regex(
            r'data-xs-id="(\d+)"', webpage, 'video id')

        data = self._download_xml(
            'http://frontend.xstream.dk/ap/feed/video/?platform=web&id=%s' % video_id, video_id)

        NS_MAP = {
            'atom': 'http://www.w3.org/2005/Atom',
            'xt': 'http://xstream.dk/',
            'media': 'http://search.yahoo.com/mrss/',
        }

        entry = data.find(xpath_with_ns('./atom:entry', NS_MAP))

        title = xpath_text(
            entry, xpath_with_ns('./atom:title', NS_MAP), 'title')
        description = xpath_text(
            entry, xpath_with_ns('./atom:summary', NS_MAP), 'description')
        timestamp = parse_iso8601(xpath_text(
            entry, xpath_with_ns('./atom:published', NS_MAP), 'upload date'))

        formats = []
        media_group = entry.find(xpath_with_ns('./media:group', NS_MAP))
        for media_content in media_group.findall(xpath_with_ns('./media:content', NS_MAP)):
            media_url = media_content.get('url')
            if not media_url:
                continue
            tbr = int_or_none(media_content.get('bitrate'))
            mobj = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>[^/]+))/(?P<playpath>.+)$', media_url)
            if mobj:
                formats.append({
                    'url': mobj.group('url'),
                    'play_path': 'mp4:%s' % mobj.group('playpath'),
                    'app': mobj.group('app'),
                    'ext': 'flv',
                    'tbr': tbr,
                    'format_id': 'rtmp-%d' % tbr,
                })
            else:
                formats.append({
                    'url': media_url,
                    'tbr': tbr,
                })
        self._sort_formats(formats)

        link = find_xpath_attr(
            entry, xpath_with_ns('./atom:link', NS_MAP), 'rel', 'original')
        if link is not None:
            formats.append({
                'url': link.get('href'),
                'format_id': link.get('rel'),
            })

        thumbnails = [{
            'url': splash.get('url'),
            'width': int_or_none(splash.get('width')),
            'height': int_or_none(splash.get('height')),
        } for splash in media_group.findall(xpath_with_ns('./xt:splash', NS_MAP))]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'formats': formats,
            'thumbnails': thumbnails,
        }
