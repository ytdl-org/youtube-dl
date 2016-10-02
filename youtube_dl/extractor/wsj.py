# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    float_or_none,
    unified_strdate,
)


class WSJIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:
            video-api\.wsj\.com/api-video/player/iframe\.html\?guid=|
            (?:www\.)?wsj\.com/video/[^/]+/
        )
        (?P<id>[a-zA-Z0-9-]+)'''
    IE_DESC = 'Wall Street Journal'
    _TESTS = [{
        'url': 'http://video-api.wsj.com/api-video/player/iframe.html?guid=1BD01A4C-BFE8-40A5-A42F-8A8AF9898B1A',
        'md5': 'e230a5bb249075e40793b655a54a02e4',
        'info_dict': {
            'id': '1BD01A4C-BFE8-40A5-A42F-8A8AF9898B1A',
            'ext': 'mp4',
            'upload_date': '20150202',
            'uploader_id': 'jdesai',
            'creator': 'jdesai',
            'categories': list,  # a long list
            'duration': 90,
            'title': 'Bills Coach Rex Ryan Updates His Old Jets Tattoo',
        },
    }, {
        'url': 'http://www.wsj.com/video/can-alphabet-build-a-smarter-city/359DDAA8-9AC1-489C-82E6-0429C1E430E0.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_url = (
            'http://video-api.wsj.com/api-video/find_all_videos.asp?'
            'type=guid&count=1&query=%s&fields=type,hls,videoMP4List,'
            'thumbnailList,author,description,name,duration,videoURL,'
            'titletag,formattedCreationDate,keywords,editor' % video_id)
        info = self._download_json(api_url, video_id)['items'][0]
        title = info.get('name', info.get('titletag'))

        formats = []

        f4m_url = info.get('videoURL')
        if f4m_url:
            formats.extend(self._extract_f4m_formats(
                f4m_url, video_id, f4m_id='hds', fatal=False))

        m3u8_url = info.get('hls')
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                info['hls'], video_id, ext='mp4',
                entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))

        for v in info.get('videoMP4List', []):
            mp4_url = v.get('url')
            if not mp4_url:
                continue
            tbr = int_or_none(v.get('bitrate'))
            formats.append({
                'url': mp4_url,
                'format_id': 'http' + ('-%d' % tbr if tbr else ''),
                'tbr': tbr,
                'width': int_or_none(v.get('width')),
                'height': int_or_none(v.get('height')),
                'fps': float_or_none(v.get('fps')),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            # Thumbnails are conveniently in the correct format already
            'thumbnails': info.get('thumbnailList'),
            'creator': info.get('author'),
            'uploader_id': info.get('editor'),
            'duration': int_or_none(info.get('duration')),
            'upload_date': unified_strdate(info.get(
                'formattedCreationDate'), day_first=False),
            'title': title,
            'categories': info.get('keywords'),
        }
