# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    compat_str,
    unified_timestamp,
)


class KakaoIE(InfoExtractor):
    _VALID_URL = r'https?://tv.kakao.com/channel/(?P<channel>\d+)/cliplink/(?P<id>\d+)'
    IE_NAME = 'kakao.com'

    _TESTS = [{
        'url': 'http://tv.kakao.com/channel/2671005/cliplink/301965083',
        'md5': '702b2fbdeb51ad82f5c904e8c0766340',
        'info_dict': {
            'id': '301965083',
            'ext': 'mp4',
            'title': '乃木坂46 バナナマン 「3期生紹介コーナーが始動！顔高低差GPも！」 『乃木坂工事中』',
            'uploader_id': 2671005,
            'uploader': '그랑그랑이',
            'timestamp': 1488160199,
            'upload_date': '20170227',
        }
    }, {
        'url': 'http://tv.kakao.com/channel/2653210/cliplink/300103180',
        'md5': 'a8917742069a4dd442516b86e7d66529',
        'info_dict': {
            'id': '300103180',
            'ext': 'mp4',
            'description': '러블리즈 - Destiny (나의 지구) (Lovelyz - Destiny)\r\n\r\n[쇼! 음악중심] 20160611, 507회',
            'title': '러블리즈 - Destiny (나의 지구) (Lovelyz - Destiny)',
            'uploader_id': 2653210,
            'uploader': '쇼 음악중심',
            'timestamp': 1485684628,
            'upload_date': '20170129',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        player_url = 'http://tv.kakao.com/embed/player/cliplink/' + video_id + \
            '?service=kakao_tv&autoplay=1&profile=HIGH&wmode=transparent'
        player_header = {'Referer': player_url}

        impress = self._download_json(
            'http://tv.kakao.com/api/v1/ft/cliplinks/%s/impress' % video_id,
            video_id, 'Downloading video info',
            query={
                'player': 'monet_html5',
                'referer': url,
                'uuid': '',
                'service': 'kakao_tv',
                'section': '',
                'dteType': 'PC',
                'fields': 'clipLink,clip,channel,hasPlusFriend,-service,-tagList'
            }, headers=player_header)

        clipLink = impress['clipLink']
        clip = clipLink['clip']

        video_info = {
            'id': video_id,
            'title': clip['title'],
            'description': clip.get('description'),
            'uploader': clipLink.get('channel', {}).get('name'),
            'uploader_id': clipLink.get('channelId'),
            'duration': int_or_none(clip.get('duration')),
            'view_count': int_or_none(clip.get('playCount')),
            'like_count': int_or_none(clip.get('likeCount')),
            'comment_count': int_or_none(clip.get('commentCount')),
        }

        tid = impress.get('tid', '')
        raw = self._download_json(
            'http://tv.kakao.com/api/v1/ft/cliplinks/%s/raw' % video_id,
            video_id, 'Downloading video formats info',
            query={
                'player': 'monet_html5',
                'referer': url,
                'uuid': '',
                'service': 'kakao_tv',
                'section': '',
                'tid': tid,
                'profile': 'HIGH',
                'dteType': 'PC',
            }, headers=player_header, fatal=False)

        formats = []
        for fmt in raw.get('outputList', []):
            try:
                profile_name = fmt['profile']
                fmt_url_json = self._download_json(
                    'http://tv.kakao.com/api/v1/ft/cliplinks/%s/raw/videolocation' % video_id,
                    video_id, 'Downloading video URL for profile %s' % profile_name,
                    query={
                        'service': 'kakao_tv',
                        'section': '',
                        'tid': tid,
                        'profile': profile_name
                    }, headers=player_header, fatal=False)

                if fmt_url_json is None:
                    continue

                fmt_url = fmt_url_json['url']
                formats.append({
                    'url': fmt_url,
                    'format_id': profile_name,
                    'width': int_or_none(fmt.get('width')),
                    'height': int_or_none(fmt.get('height')),
                    'format_note': fmt.get('label'),
                    'filesize': int_or_none(fmt.get('filesize'))
                })
            except KeyError:
                pass

        self._sort_formats(formats)
        video_info['formats'] = formats

        top_thumbnail = clip.get('thumbnailUrl')
        thumbs = []
        for thumb in clip.get('clipChapterThumbnailList', []):
            thumbs.append({
                'url': thumb.get('thumbnailUrl'),
                'id': compat_str(thumb.get('timeInSec')),
                'preference': -1 if thumb.get('isDefault') else 0
            })
        video_info['thumbnail'] = top_thumbnail
        video_info['thumbnails'] = thumbs

        upload_date = unified_timestamp(clipLink.get('createTime'))
        video_info['timestamp'] = upload_date

        return video_info
