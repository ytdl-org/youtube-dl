# coding: utf-8
from __future__ import unicode_literals

import base64
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    smuggle_url
)


class PutLockerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?putlocker\.is/(?P<id>[^/]+)\.html'
    _TESTS = [
        {
            'url': 'http://putlocker.is/watch-the-silence-of-the-lambs-online-free-putlocker.html',
            'md5': 'ad624b58450625faf64762b72b8ecb0d',
            'info_dict': {
                'id': 'the-silence-of-the-lambs',
                'ext': 'mp4',
                'title': 'The Silence of the Lambs',
                'description': ('Young FBI agent Clarice Starling is assigned to help find a missing '
                                'woman to save her from a psychopathic serial killer who skins his victims. Clarice '
                                'attempts to gain a better insight into the twisted mind of the killer by talking to '
                                'another psychopath Hannibal Lecter, who used to be a respected psychiatrist. FBI agent '
                                'Jack Crawford believes that Lecter, who is also a very powerful and clever mind '
                                'manipulator, has the answers to their questions and can help locate the killer. '
                                'However, Clarice must first gain Lecter\'s confidence before the inmate will give away '
                                'any information.'),
                'thumbnail': 'http://image4.putlocker.is/images/covers/the-silence-of-the-lambs-online-free-putlocker.jpg',
                'height': 410,
                'width': 728,
                'uploader': 'thevideos.tv'
            }
        },
        {
            'url': 'http://putlocker.is/watch-arrested-development-tvshow-season-1-episode-1-online-free-putlocker.html',
            'md5': '7afdf6e99831757dbcc3eb28f9da6f7b',
            'info_dict': {
                'id': 'arrested-development-tvshow-season-1-episode-1',
                'ext': 'mp4',
                'title': 'Arrested Development Season 1 Episode 1: Pilot',
                'description': ('Widower Michael Bluth has been working for his father\'s development '
                                'company since he was a teenager manning the family\'s frozen banana stand, and he '
                                'and his son George Michael have gone so far as to move into one of the company\'s '
                                'model homes. So when his father George Sr. throws his retirement party on the family '
                                'yacht, Michael expects that he will be announced as his father\'s successor. Instead, '
                                'Michael gets two surprises: His mother is the new President, and his father is under '
                                'investigation by the SEC. So Michael has to hold his wildly dysfunctional family together.'),
                'thumbnail': 'http://image4.putlocker.is/images/covers/arrested-development-tvshow-season-1-episode-1-online-free-putlocker.jpg',
                'height': 410,
                'width': 728,
                'uploader': 'thevideos.tv'
            }
        },
        {
            'url': 'http://putlocker.is/watch-community-tvshow-season-3-episode-4-online-free-putlocker.html',
            'md5': 'c34b6561ef5e2be973f0e2b6f33095d5',
            'info_dict': {
                'id': 'community-tvshow-season-3-episode-4',
                'ext': 'mp4',
                'title': 'Community Season 3 Episode 4: Remedial Chaos Theory',
                'description': ('When Troy and Abed decide to share an apartment, they host a party for '
                                'the group, which takes on an altered reality as several scenarios play out.'),
                'thumbnail': 'http://image4.putlocker.is/images/covers/community-tvshow-season-3-episode-4-online-free-putlocker.jpg',
                'height': 410,
                'width': 728,
                'uploader': 'thevideos.tv'
            }
        }
    ]

    def trim_string(self, string, start='', end=''):
        if start and string.startswith(start):
            string = string[len(start):]

        if end and string.endswith(end):
            string = string[:-len(end)]

        return string

    def extract_url_id(self, url):
        url_id = self._match_id(url)

        # Try to remove generic substrings before and after the interesting section
        return self.trim_string(
            url_id, 'watch-', '-online-free-putlocker')

    def extract_webpage_title(self, webpage):
        video_title = self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, 'video title')

        # Try to remove generic substrings before and after the title
        return self.trim_string(
            video_title, 'Watch ',
            ' Online Free Putlocker | Putlocker - Watch Movies Online Free')

    def extract_webpage_description(self, webpage):
        description = self._html_search_regex(
            r'(?s)<strong>Synopsis:</strong>[ ]?(.*?)</td>', webpage, 'video description')

        # A generic phrase but by Putlocker should appear before the actual description.
        # We try to find it and return the rest of the description
        arr = description.split(' Putlocker. ')

        # Too many 'Putlocker' substrings found, this shouldn't happen. Return everything
        if (len(arr) > 2):
            return description

        # If the 'Putlocker' substring was not found that's fine, everything is returned
        return arr[-1]

    def _real_extract(self, url):
        video_id = self.extract_url_id(url)

        webpage = self._download_webpage(url, video_id)

        encoded_matches = re.findall(r'document\.write\(doit\(\'(.+)\'\)\)', webpage)

        # Every match is html to inject into the page, encoded in base64
        # twice. Only one will be the valid video URL, other content (such
        # as ads) also loaded this way.
        for encoded in encoded_matches:
            html = base64.b64decode(base64.b64decode(encoded))

            iframe_match = re.search(r'<iframe src="(\S+)"', html)

            if not iframe_match:
                continue

            video_url = iframe_match.group(1)

            # The expected iframe url is from thevideos.tv, which can be extracted with
            # the generic IE
            url_match = re.search(r'thevideos\.tv/(?:embed-)?.+-(\d+)x(\d+)\.html', video_url)

            if not url_match:
                continue

            # http://thevideos.tv/embed-bdntjxryinrg-728x410.html
            width = int(url_match.group(1))
            height = int(url_match.group(2))
            break

        if not url_match:
            # If the url inside the iframe wasn't the expected one, we can't extract any
            # extra information about the video being downloaded. We try to fall back to
            # the generic IE. This case hasn't been seen, there are no tests for it.
            if video_url:
                return {
                    '_type': 'url',
                    'url': video_url
                }
            # No encoded data was found, or it didn't contain an iframe. Nothing to do,
            # return an error.
            else:
                raise ExtractorError('Unable to extract video URL')

        return {
            '_type': 'url_transparent',
            # Intentionally fall back to generic extractor, it extracts
            # thevideos.tv videos correctly
            'url': smuggle_url(video_url, {'to_generic': True}),
            'id': video_id,
            'title': self.extract_webpage_title(webpage),
            'description': self.extract_webpage_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'width': width,
            'height': height
        }
