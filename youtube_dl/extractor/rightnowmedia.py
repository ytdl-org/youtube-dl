from __future__ import unicode_literals
import re
from ..compat import compat_urllib_parse_unquote
from .common import InfoExtractor
from ..utils import (
    determine_ext,
)


class RightNowMediaIE(InfoExtractor):
    IE_NAME = 'rightnowmedia'
    _VALID_URL = r'https?://(?:www\.)?rightnowmedia\.org/Content/(?P<id>[0-9]+)/(?:downloadAndEmbed)'
    _TEST = {
        'url': 'https://www.rightnowmedia.org/Content/293653/downloadAndEmbed',
        'info_dict': {
            'id': '293653',
            'ext': 'mp4',
            'title': ' Philippians 1_12-18 - HD 1080p',
        }
    }

    def _real_extract(self, url):
        # Video Id
        video_id = self._match_id(url)

        # Download
        video_info_dicts = self._download_json(
            'https://www.rightnowmedia.org/Content/%s/downloadAndEmbed'
            % video_id, video_id)

        # Get All The Formats
        formats = []
        for video_info in video_info_dicts['downloadLinks']:
            quality = 'high' if 'HD 1080p' in video_info["QualityName"] else 'low'
            formats.append({
                'url': video_info["Link"],
                'preference': 10 if quality == 'high' else 0,
                'format_note': quality,
                'format_id': '%s-%s' % (quality, determine_ext(video_info["Link"])),
            })

        # Get the Title
        title = compat_urllib_parse_unquote(re.findall(
            r'.*?filename=(.*).*(?:.mp4)',
            formats[0]['url'])[0])

        # Sort Formats
        self._sort_formats(formats)

        # Return
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }


class RightNowMediaPlaylistIE(InfoExtractor):
    IE_NAME = 'rightnowmedia:playlist'
    _VALID_URL = r'https?://(?:www\.)?rightnowmedia\.org/Content/(?:Series|KidsShow)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.rightnowmedia.org/Content/Series/265320',
        'info_dict': {
            'id': '265320'
        },
        'playlist_count': 9,
    }, {
        'url': 'https://www.rightnowmedia.org/Content/KidsShow/298875',
        'info_dict': {
            'id': '298875'
        },
        'playlist_count': 15,
    }]

    def _real_extract(self, url):
        # Series Id
        playlist_id = self._match_id(url)

        # Download Webpage
        webpage = self._download_webpage(url, playlist_id)

        # Find The Correct Table
        all_buckets = re.findall(
            r'(?s)<table [^"]*"..*? id="primarySeriesTable" [^"]*"..*? \B.*\B<div class="row rowStripMargin nomobile">',
            webpage)

        # Find All The Video Elements
        all_video_elements = re.findall(
            r'.*?data-detail-content-id="(.*)">.*',
            all_buckets[0])

        # Finalize All The URLs
        entries = []
        for video_element in all_video_elements:
            entries.append(self.url_result('https://www.rightnowmedia.org/Content/%s/downloadAndEmbed' % video_element))

        # Return
        return {
            '_type': 'playlist',
            'id': playlist_id,
            'entries': entries,
        }
