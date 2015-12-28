# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    float_or_none,
)


class TenPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ten(play)?\.com\.au/.+'
    _TEST = {
        'url': 'http://tenplay.com.au/ten-insider/extra/season-2013/tenplay-tv-your-way',
        'info_dict': {
            'id': '2695695426001',
            'ext': 'flv',
            'title': 'TENplay: TV your way',
            'description': 'Welcome to a new TV experience. Enjoy a taste of the TENplay benefits.',
            'timestamp': 1380150606.889,
            'upload_date': '20130925',
            'uploader': 'TENplay',
        },
        'params': {
            'skip_download': True,  # Requires rtmpdump
        }
    }

    _video_fields = [
        "id", "name", "shortDescription", "longDescription", "creationDate",
        "publishedDate", "lastModifiedDate", "customFields", "videoStillURL",
        "thumbnailURL", "referenceId", "length", "playsTotal",
        "playsTrailingWeek", "renditions", "captioning", "startDate", "endDate"]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, url)
        video_id = self._html_search_regex(
            r'videoID: "(\d+?)"', webpage, 'video_id')
        api_token = self._html_search_regex(
            r'apiToken: "([a-zA-Z0-9-_\.]+?)"', webpage, 'api_token')
        title = self._html_search_regex(
            r'<meta property="og:title" content="\s*(.*?)\s*"\s*/?\s*>',
            webpage, 'title')

        json = self._download_json('https://api.brightcove.com/services/library?command=find_video_by_id&video_id=%s&token=%s&video_fields=%s' % (video_id, api_token, ','.join(self._video_fields)), title)

        formats = []
        for rendition in json['renditions']:
            url = rendition['remoteUrl'] or rendition['url']
            protocol = 'rtmp' if url.startswith('rtmp') else 'http'
            ext = 'flv' if protocol == 'rtmp' else rendition['videoContainer'].lower()

            if protocol == 'rtmp':
                url = url.replace('&mp4:', '')

                tbr = int_or_none(rendition.get('encodingRate'), 1000)

            formats.append({
                'format_id': '_'.join(
                    ['rtmp', rendition['videoContainer'].lower(),
                     rendition['videoCodec'].lower(), '%sk' % tbr]),
                'width': int_or_none(rendition['frameWidth']),
                'height': int_or_none(rendition['frameHeight']),
                'tbr': tbr,
                'filesize': int_or_none(rendition['size']),
                'protocol': protocol,
                'ext': ext,
                'vcodec': rendition['videoCodec'].lower(),
                'container': rendition['videoContainer'].lower(),
                'url': url,
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': json['referenceId'],
            'title': json['name'],
            'description': json['shortDescription'] or json['longDescription'],
            'formats': formats,
            'thumbnails': [{
                'url': json['videoStillURL']
            }, {
                'url': json['thumbnailURL']
            }],
            'thumbnail': json['videoStillURL'],
            'duration': float_or_none(json.get('length'), 1000),
            'timestamp': float_or_none(json.get('creationDate'), 1000),
            'uploader': json.get('customFields', {}).get('production_company_distributor') or 'TENplay',
            'view_count': int_or_none(json.get('playsTotal')),
        }
