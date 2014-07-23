# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TenPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ten(play)?\.com\.au/.+'
    _TEST = {
        'url': 'http://tenplay.com.au/ten-insider/extra/season-2013/tenplay-tv-your-way',
        #'md5': 'd68703d9f73dc8fccf3320ab34202590',
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

            formats.append({
                'format_id': '_'.join(['rtmp', rendition['videoContainer'].lower(), rendition['videoCodec'].lower()]),
                'width': rendition['frameWidth'],
                'height': rendition['frameHeight'],
                'tbr': rendition['encodingRate'] / 1024,
                'filesize': rendition['size'],
                'protocol': protocol,
                'ext': ext,
                'vcodec': rendition['videoCodec'].lower(),
                'container': rendition['videoContainer'].lower(),
                'url': url,
            })

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
            'duration': json['length'] / 1000,
            'timestamp': float(json['creationDate']) / 1000,
            'uploader': json['customFields']['production_company_distributor'] if 'production_company_distributor' in json['customFields'] else 'TENplay',
            'view_count': json['playsTotal']
        }
