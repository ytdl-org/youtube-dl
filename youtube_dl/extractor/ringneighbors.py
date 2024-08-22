# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    urljoin,
)


class RingNeighborsIE(InfoExtractor):
    IE_NAME = 'ringneighbors'
    IE_DESC = 'Surveillance video from a shared link from Neighbors (app within Ring)'
    _VALID_URL = r'https?://neighbors\.ring\.com/n/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'https://neighbors.ring.com/n/oEdj2',
        'md5': '4f9038a4a926dea5db3d399d0326abe7',
        'info_dict': {
            'id': 'oEdj2',
            'ext': 'mp4',
            'title': 'Ding Dong Ditch is alive and well',
            'thumbnail': 'https://neighbors.ring.com/assets/images/default_og_image.png',
            'upload_date': '20180210',
            'location': '4721 Indian Deer Rd, Windermere, FL 34786, USA',
            'description': 'Get crime and safety alerts from your neighbors',
            'timestamp': 1518298052,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        url = self._html_search_regex(r'<input[^>]+value="(?P<url>https?://share.ring.com/[^\.]+\.mp4)"',
                                      webpage,
                                      'url',
                                      group='url')
        dt = self._html_search_regex('<span[^>]+class="event\-date">(?P<event_date>[^<]+)',
                                     webpage,
                                     'Event date (ISO 8601)',
                                     group='event_date',
                                     fatal=False)
        loc = self._html_search_regex('<span[^>]+class="event\-address">(?P<address>[^<]+)',
                                      webpage,
                                      'Location',
                                      group='address',
                                      fatal=False)
        upload_date = None
        if dt:
            upload_date = dt[0:10].replace('-', '')
        base = 'https://neighbors.ring.com/'
        thumbnail = urljoin(base, self._og_search_thumbnail(webpage))

        return {
            'id': video_id,
            'title': self._og_search_property('title', webpage).strip(),
            'url': url,
            'ext': determine_ext(url),
            'description': self._html_search_meta('description', webpage, 'Description'),
            'upload_date': upload_date,
            'release_date': upload_date,
            'timestamp': int_or_none(parse_iso8601(dt)),
            'location': loc,
            'thumbnail': thumbnail,
        }
