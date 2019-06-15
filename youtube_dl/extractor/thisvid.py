# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from .openload import PhantomJSwrapper


class ThisVidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisvid\.com/videos/(?P<id>[A-Za-z0-9-]+)'

    _TEST = {
        'url': 'https://thisvid.com/videos/madonna-show-in-sexy-underwear/',
        'md5': '48e38730d38394c6e9f1cce66fb04c6e',
        'info_dict': {
            'id': '829503',
            'display_id': 'madonna-show-in-sexy-underwear',
            'ext': 'mp4',
            'title': 'Madonna show in sexy underwear',
            'thumbnail': r're:^https?://.*preview\.mp4\.jpg$',
            'uploader_id': 'Mike_Hunt',
            'uploader_url': 'https://thisvid.com/members/584768',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        # The webpage contains a raw piece of javascript which creates a
        # variable called flashvars used by the player to update the webpage.
        #
        # Running the javascript fixes the URL in the static HTML which is
        # broken, and updates the flashvars variable with the new info.
        #
        # Because there are a ton of errors from PhantomJS that do not affect
        # the output, they have to be split from the actual JSON.
        jscode = """
        function checkFlashVars() {
            flashvars = page.evaluate(function() {
                return JSON.stringify(flashvars)
            });
            console.log('---'); // ensure any errors appear above where we are
            console.log(flashvars);
            saveAndExit();
        }
        checkFlashVars();"""
        phantom = PhantomJSwrapper(self, required_version='2.0')
        webpage, output = phantom.get(url, html=webpage, jscode=jscode)
        flashvars = self._parse_json(output.split("---", 2)[1], display_id)

        # Get the video URL from the flashvars.
        video_url = flashvars['video_url']

        # The value in the static HTML starts with "function/0/http://..."
        # where the zero is sometimes another number.
        #
        # At try that static URL if there was a static update failure.
        if video_url.startswith('function'):
            self.report_warning('Page JS failed, fetch will likely fail')
            video_url = video_url.split("/", 3)[2]

        # Sometimes the video url ends with ".mp4",
        # other times it ends with ".mp4/",
        # yet other times it ends with ".mp4/?".
        #
        # All of it needs to be cleaned up.
        video_url = video_url.split("?", 2)[0].strip("/")

        # Get the thumbnail URL from the flashvars.
        thumbnail_url = flashvars['preview_url']

        # The thumbnail usually does not have a protocol on the front, e.g.
        # "//media.thisvid.com"
        if thumbnail_url.startswith("//"):
            thumbnail_url = 'https:' + thumbnail_url

        # The simplest way to get the real internal ID is to get it from the
        # URL we will be accessing.
        video_id = video_url.split("/")[-2]

        # Parse the title information.
        title = self._search_regex(r'<title>(?P<title>.+) -([a-zA-Z ]+ at)? ThisVid(\.com| tube)</title>',
                                   webpage, display_id, group='title')

        # Parse the author information from a profile link.
        author_re = r'<a.*class="author" href="(?P<url>[^"]+)"[^>]*>(?P<id>[^<]+)</a'
        uploader_id = self._search_regex(author_re, webpage, display_id,
                                         group='id')
        uploader_url = self._search_regex(author_re, webpage, display_id,
                                          group='url').strip("/")

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'url': video_url,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'thumbnail': thumbnail_url,
            'age_limit': 18,
        }


class ThisVidEmbeddedIE(ThisVidIE):
    _VALID_URL = r'https?://(?:www\.)?thisvid\.com/embed/(?P<id>[A-Za-z0-9-]+)'
    _TEST = {
        'url': 'https://thisvid.com/embed/854312',
        'md5': '8166497c0281b54a48b179c997463892',
        'info_dict': {
            'id': '854312',
            'display_id': 'soles-of-jaxwheeler',
            'ext': 'mp4',
            'title': 'Soles of JaxWheeler',
            'thumbnail': r're:^https?://.*preview\.mp4\.jpg$',
            'uploader_id': 'SNK13',
            'uploader_url': 'https://thisvid.com/members/252887',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        embedded_page = self._download_webpage(url, video_id)
        full_url = self._search_regex(
                r'<link rel="canonical" href="(?P<href>[^"]+)"',
                embedded_page, video_id, group='href')
        video_id = full_url.strip("/").rsplit("/", 1)[-1]
        return self.url_result(full_url, video_id=video_id)
