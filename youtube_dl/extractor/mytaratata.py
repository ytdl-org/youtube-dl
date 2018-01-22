# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MyTaratataIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mytaratata\.com/taratata/(?P<id>[a-zA-Z0-9_\-/]+)'
    _TEST = {
        'url': 'http://mytaratata.com/taratata/519/shaka-ponk-camille-et-julie-berthollet-smells-like-teen-spirit-nirvana',
        'md5': '99657330eb7dec6d63a329d7f26ec93e',
        'info_dict': {
            'id': '7174',
            'ext': 'mp4',
            'title': 'TARATATA N°519 - Shaka Ponk / Camille et Julie Berthollet "Smells Like Teen Spirit" (Nirvana)',
            'uploader': 'Taratata',
            'description': 'Shaka Ponk / Camille et Julie Berthollet "Smells Like Teen Spirit" (Nirvana)',
            'thumbnail': 're:https?://.*\.jpeg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # The title contains only the program name and episode number.
        # Each episode containts many videos
        title = self._og_search_title(webpage)
        # The description is the title of the video within the episode.
        description = self._og_search_description(webpage)

        formats = []

        video_source_re = re.compile(
            r'<div [^>]*class="jwplayer" [^\>]*data-source="(?P<url>[^"]+)"'
        )

        # The first videos are the live videos, coming in 2 formats. The next videos are
        # bonuses, multi-cams... that we won't download.
        last_vid = None
        for video_url in video_source_re.findall(webpage):
            info_m = re.match(
                r'.*/(?P<vid>[0-9]+)-[a-f0-9]+-(?P<w>[0-9]+)x(?P<h>[0-9]+)\.mp4',
                video_url)
            if info_m is None:
                continue
            vid = info_m.group('vid')
            w = info_m.group('w')
            h = info_m.group('h')

            if last_vid is None:
                last_vid = vid

            if vid != last_vid:
                # We found a new video, not another format of the same. Stops here.
                break

            formats.append({
                'url': video_url,
                'width': int(w),
                'height': int(h),
            })

        self._sort_formats(formats)

        return {
            'id': last_vid,
            'title': '%s - %s' % (title, description),
            'description': description,
            'uploader': "Taratata",
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
        }
