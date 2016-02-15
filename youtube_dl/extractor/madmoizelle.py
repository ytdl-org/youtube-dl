# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MadmoizelleIE(InfoExtractor):
    IE_NAME = 'madmoizelle.com'
    IE_DESC = 'madmoizelle.com video:article'
    _VALID_URL = r'https?://(?:www\.)?madmoizelle\.com/.+-(?P<id>[0-9]+)#?.*'
    _TESTS = [{
        # site's video in banner
        'url': 'http://www.madmoizelle.com/american-ultra-marion-seclin-408959#gs.nNBitsc',
        'info_dict': {
            'ext': 'mp4',
            'id': '408959',
            'title': 'Ma vie, c\'est comme dans American Ultra (Marion Seclin)',
            'description': 'md5:af3f8fc3b0668ede24feb1d50826e00c',
        }
    }, {
        # external video in banner
        'url': 'http://www.madmoizelle.com/game-of-thrones-saison-5-podcast-383647#gs.MvCyYtg',
        'info_dict': {
            'ext': 'mp4',
            'description': 'md5:efe603274fe803d27f9cb912eb83491a',
            'title': 'REPLAY ! L\'éMymyssion - Bilan Game of Thrones saison 5',
            'id': 'hH__bkW5Hu0',
            'upload_date': '20150623',
            'uploader_id': 'madmoiZelledotcom',
            'uploader': 'madmoiZelle.com',
        },
    }, {
        # site's video in banner and external video in content
        'url': 'http://www.madmoizelle.com/ukulete-episode-1-408599',
        'md5': 'e79ce7c2131cb3dfd200bea5177236fe',
        'info_dict': {
            'ext': 'mp4',
            'id': '408599',
            'title': 'Ukul’été - Épisode 1 - Plus besoin de radio !',
            'description': 'md5:18949f6512cbd285c7b8b536a9955f06',
        }
    }, {
        # external video in content
        'url': 'http://www.madmoizelle.com/connected-court-metrage-501199#gs.AblS7VA',
        'md5': '320890bbce5968e3482059a5d3770ba9',
        'info_dict': {
            'title': '\'Connected\' - A Sci-Fi Short Starring Pamela Anderson',
            'id': 'iWLcWHYmgpg',
            'ext': 'mp4',
            'upload_date': '20160208',
            'description': 'md5:8de82e60853651512fb923e84873f526',
            'uploader': 'Motherboard',
            'uploader_id': 'MotherboardTV',
            'age_limit': 18,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # all article page may contain one video in a banner form,
        # and many externals videos in the article content
        results = []

        if '<div class="video_single">' in webpage:
            # banner video present
            title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
            description = self._html_search_meta('description', webpage)
            formats = []
            for format in re.finditer('jwplayer.*"(?P<url>[0-9]+.*(?P<quality>hd|sd).+)"', webpage):
                formats.append({
                    'format_id': format.group('quality'),
                    'url': 'https://player.vimeo.com/external/' + format.group('url'),
                })

            if formats:
                # site's jw player url found
                results.append({
                    'formats': formats,
                    'id': video_id,
                    'title': title,
                    'description': description,
                })

        # external video, may be any site, in any number
        # fallback to generic extractor
        for external_vid in re.finditer(r'<iframe.*src="(?P<url>.*?)".*</iframe>', webpage):
            results.append({
                'url': external_vid.group('url'),
                '_type': 'url',
            })

        return {
            '_type': 'playlist',
            'entries': results,
        }
