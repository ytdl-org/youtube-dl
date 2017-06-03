# coding: utf-8
from __future__ import unicode_literals

import lxml.html

from .common import InfoExtractor


class OnePieceTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?onepiece-tube\.com/folge/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://onepiece-tube.com/folge/778',
        'md5': 'f95e52a89071c1997ef809607f106ec5',
        'info_dict': {
            'id': '778',
            'ext': 'mp4',
            'title': 'One Piece 778 - Zur Weltkonferenz! Rebecca und das Sakura Königreich!',
            'series': 'One Piece',
            'episode': '778',
            'thumbnail': 'http://cdn.ani-stream.com/thumb/4rt9j41nplak.jpg'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, 'OnePiece-Tube')

        # Compose title information so far
        pre_title = 'One Piece ' + str(video_id)

        # Use XPath to determine title
        root = lxml.html.fromstring(webpage)
        title = None

        # Try HTML title
        for elem in root.xpath('//head/title/text()'):
            title = elem
            break

        # Try meta information title
        if title is None:
            for elem in root.xpath('//meta[@name="title"]/@content'):
                title = elem
                break

        # Try content-heading
        if title is None:
            for elem in root.xpath('//[@class="contentheading"]/text()'):
                title = elem
                break
        # If no specific title is found, use solely pre-title
        if title is None:
            title = pre_title
        else:
            # Sanitise title
            title = title.split('|')[-1].strip()
            # Compose
            title = pre_title + ' - ' + title

        # Use XPath to determine url of embedded video
        embed_url = None
        for elem in root.xpath('//*[@id="embed"]/iframe/@src'):
            embed_url = elem
            break

        # Download embedded webpage
        webpage = self._download_webpage(embed_url, 'anistream.com')

        # Get real location of file
        url = self._search_regex(r'file: ["\'](?P<url>https?://[a-zA-Z0-9/\-\.]*?.mp4)["\']', webpage, 'url', group='url')

        # Get Thumbnail
        thumbnail = 'http:' + self._search_regex(r'image: ["\'](?P<thumb>//[a-zA-Z0-9/\-\.]*?.jpg)["\']', webpage, 'thumb', group='thumb', default=None)

        # Return video information dict
        return {
            'id': video_id,
            'title': title,
            'url': url,
            'series': 'One Piece',
            'episode': video_id,
            'thumbnail': thumbnail,
        }
