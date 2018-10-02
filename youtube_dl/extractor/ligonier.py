# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class LigonierIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ligonier\.org/learn/(?P<id>.*)'
    _TESTS = [
        {
            'url': 'https://www.ligonier.org/learn/daily-video/2018/10/01/a-permanent-birth/',
            'info_dict': {
                'id': 'a-permanent-birth',
                'description': "Ironically, we can become so afraid of losing something that we no longer fully enjoy having it. This is true in both everyday affairs and in spiritual matters. People will sometimes keep a prized possession out of harm's way to such an extent that they no longer use it or enjoy it. Fortunately, Christians can rejoice in the knowledge that the forgiveness of sins, their relationship with God, and their eternal hope can never be taken away. Few truths are as beautiful as God's promise that those who are born again receive a permanent birth and can never lose their status as His sons and daughters.",
                'ext': 'mp4',
                'title': 'A Permanent Birth by Steven Lawson | October 1, 2018',
                'thumbnail': r're:^https?://.*\.jpg$',
            }
        },
        {
            'url': 'https://www.ligonier.org/learn/series/learning-love-psalms/introduction-part-1-attractions-difficulties/?',
            'info_dict': {
                'id': 'introduction-part-1-attractions-difficulties',
                'description': "The Psalms have a Godward direction, being God&rsquo;s words to us to give back to Him. In this lesson, Dr. Godfrey discusses the uniqueness of the Psalms as well as the difficulties that must be overcome if we are to learn to love them.",
                'ext': 'mp4',
                'title': 'Introduction (Part 1): Attractions & Difficulties by W. Robert Godfrey',
                'thumbnail': r're:^https?://.*\.jpg$',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._getId(url)
        webpage = self._download_webpage(url, video_id)
        url = self._html_search_regex(r"{\"file\":\s?\"(?P<url>https?:.[^\"]*)\"", webpage, 'url')
        thumbnail = self._html_search_regex(r"\"image\":\s?\"(?P<url>https?:.[^\"]*)\"", webpage, 'thumbnail')
        return {
            'id': video_id,
            'url': url,
            'thumbnail': thumbnail,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'format': 'mp4',
        }

    def _getId(self, url):
        matched_string = self._match_id(url)
        return matched_string.rstrip('/?').split('/')[-1]
