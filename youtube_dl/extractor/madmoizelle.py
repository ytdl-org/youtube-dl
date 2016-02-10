# coding: utf-8
from __future__ import unicode_literals

import re
from ..utils import HEADRequest

from .common import InfoExtractor


class MadmoizelleIE(InfoExtractor):
    _VALID_URL = r'(https?://)?(?:www\.)?madmoizelle\.com/(?P<descr>.+)-(?P<id>[0-9]+)#?.*'
    _TESTS = [{
        # classic video from the site
        'url': 'http://www.madmoizelle.com/ukulete-episode-1-408599',
        'md5': 'e79ce7c2131cb3dfd200bea5177236fe',
        'info_dict': {
            'ext': 'mp4',
            'id': '408599',
            'title': 'Ukul’été - Épisode 1 - Plus besoin de radio !',
        }
    }, {
        # to test youtube redirection fallback
        'url': 'http://www.madmoizelle.com/connected-court-metrage-501199#gs.AblS7VA',
        'md5': '77928d3964eceb2fe828204db5ee714a',
        'info_dict': {
            'title': '\'Connected\' - A Sci-Fi Short Starring Pamela Anderson',
            'id': 'iWLcWHYmgpg',
            'ext': 'mp4',
            'upload_date': '20160208',
            'description': 'md5:8de82e60853651512fb923e84873f526',
            'uploader': 'Motherboard',
            'uploader_id': 'MotherboardTV',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # find title
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        # find all format, despite the main player of the site being differrent JW player by quality
        formats = []
        for format in re.finditer('jwplayer.*"(?P<url>[0-9]+.*(?P<quality>hd|sd).+)"', webpage):
            url = 'https://player.vimeo.com/external/' + format.group('url')
            formats.append({
                'format_id': format.group('quality'),
                'url': url,
            })

        if not formats:
            # nothing has been found with the site's extractor,
            # fallback to generic with original url as the website
            # embed different source such as youtube
            return {
                'url': url,
                'ie_key': 'Generic',
                '_type': 'url',
            }

        # choose HD by default.
        url = formats[-1]['url']  # HD choose by default

        # the url found has a header redirection that we follow
        head_req = HEADRequest(url)
        head_response = self._request_webpage(
            head_req, video_id,
            note=False, errnote='Could not send HEAD request to %s' % url,
            fatal=False)
        if head_response is not False:
            url = (self.url_result(head_response.geturl()))['url']

        return {
            'url': url,
            'ie_key': 'Generic',
            'id': video_id,
            'title': title,
        }
