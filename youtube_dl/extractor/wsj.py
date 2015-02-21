# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class WSJIE(InfoExtractor):
    _VALID_URL = r'https?://video-api\.wsj\.com/api-video/player/iframe\.html\?guid=(?P<id>[a-zA-Z0-9-]+)'
    IE_DESC = 'Wall Street Journal'
    _TEST = {
        'url': 'http://video-api.wsj.com/api-video/player/iframe.html?guid=1BD01A4C-BFE8-40A5-A42F-8A8AF9898B1A',
        'md5': '9747d7a6ebc2f4df64b981e1dde9efa9',
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
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        bitrates = [128, 174, 264, 320, 464, 664, 1264]
        api_url = (
            'http://video-api.wsj.com/api-video/find_all_videos.asp?'
            'type=guid&count=1&query=%s&'
            'fields=hls,adZone,thumbnailList,guid,state,secondsUntilStartTime,'
            'author,description,name,linkURL,videoStillURL,duration,videoURL,'
            'adCategory,catastrophic,linkShortURL,doctypeID,youtubeID,'
            'titletag,rssURL,wsj-section,wsj-subsection,allthingsd-section,'
            'allthingsd-subsection,sm-section,sm-subsection,provider,'
            'formattedCreationDate,keywords,keywordsOmniture,column,editor,'
            'emailURL,emailPartnerID,showName,omnitureProgramName,'
            'omnitureVideoFormat,linkRelativeURL,touchCastID,'
            'omniturePublishDate,%s') % (
                video_id, ','.join('video%dkMP4Url' % br for br in bitrates))
        info = self._download_json(api_url, video_id)['items'][0]

        # Thumbnails are conveniently in the correct format already
        thumbnails = info.get('thumbnailList')
        creator = info.get('author')
        uploader_id = info.get('editor')
        categories = info.get('keywords')
        duration = int_or_none(info.get('duration'))
        upload_date = unified_strdate(
            info.get('formattedCreationDate'), day_first=False)
        title = info.get('name', info.get('titletag'))

        formats = [{
            'format_id': 'f4m',
            'format_note': 'f4m (meta URL)',
            'url': info['videoURL'],
        }]
        if info.get('hls'):
            formats.extend(self._extract_m3u8_formats(
                info['hls'], video_id, ext='mp4',
                preference=0, entry_protocol='m3u8_native'))
        for br in bitrates:
            field = 'video%dkMP4Url' % br
            if info.get(field):
                formats.append({
                    'format_id': 'mp4-%d' % br,
                    'container': 'mp4',
                    'tbr': br,
                    'url': info[field],
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'thumbnails': thumbnails,
            'creator': creator,
            'uploader_id': uploader_id,
            'duration': duration,
            'upload_date': upload_date,
            'title': title,
            'formats': formats,
            'categories': categories,
        }
