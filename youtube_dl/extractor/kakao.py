# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    unified_timestamp,
    update_url_query,
    ExtractorError
)


class KakaoIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.kakao\.com/channel/(?P<channel>\d+)/cliplink/(?P<id>\d+)'
    _API_BASE = 'http://tv.kakao.com/api/v1/ft'

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

        playlist_id = self._search_regex(r'playlistId=(\d+)', url, 'channel_id', default=None)
        if playlist_id:
            if not self._downloader.params.get('noplaylist'):
                chan_id = self._search_regex(r'channel/(\d+)', url, 'playlist_id')
                self.to_screen('Downloading playlist %s - add --no-playlist to just download video' % playlist_id)
                return self.url_result(
                    'http://tv.kakao.com/channel/%s/playlist/%s' % (chan_id, playlist_id)
                )
            else:
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        player_header = {
            'Referer': update_url_query(
                'http://tv.kakao.com/embed/player/cliplink/%s' % video_id, {
                    'service': 'kakao_tv',
                    'autoplay': '1',
                    'profile': 'HIGH',
                    'wmode': 'transparent',
                })
        }

        QUERY_COMMON = {
            'player': 'monet_html5',
            'referer': url,
            'uuid': '',
            'service': 'kakao_tv',
            'section': '',
            'dteType': 'PC',
        }

        query = QUERY_COMMON.copy()
        query['fields'] = 'clipLink,clip,channel,hasPlusFriend,-service,-tagList'
        impress = self._download_json(
            '%s/cliplinks/%s/impress' % (self._API_BASE, video_id),
            video_id, 'Downloading video info',
            query=query, headers=player_header)

        clip_link = impress['clipLink']
        clip = clip_link['clip']

        title = clip.get('title') or clip_link.get('displayTitle')

        tid = impress.get('tid', '')

        query = QUERY_COMMON.copy()
        query.update({
            'tid': tid,
            'profile': 'HIGH',
        })
        raw = self._download_json(
            '%s/cliplinks/%s/raw' % (self._API_BASE, video_id),
            video_id, 'Downloading video formats info',
            query=query, headers=player_header)

        formats = []
        for fmt in raw.get('outputList', []):
            try:
                profile_name = fmt['profile']
                fmt_url_json = self._download_json(
                    '%s/cliplinks/%s/raw/videolocation' % (self._API_BASE, video_id),
                    video_id,
                    'Downloading video URL for profile %s' % profile_name,
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

        thumbs = []
        for thumb in clip.get('clipChapterThumbnailList', []):
            thumbs.append({
                'url': thumb.get('thumbnailUrl'),
                'id': compat_str(thumb.get('timeInSec')),
                'preference': -1 if thumb.get('isDefault') else 0
            })
        top_thumbnail = clip.get('thumbnailUrl')
        if top_thumbnail:
            thumbs.append({
                'url': top_thumbnail,
                'preference': 10,
            })

        return {
            'id': video_id,
            'title': title,
            'description': clip.get('description'),
            'uploader': clip_link.get('channel', {}).get('name'),
            'uploader_id': clip_link.get('channelId'),
            'thumbnails': thumbs,
            'timestamp': unified_timestamp(clip_link.get('createTime')),
            'duration': int_or_none(clip.get('duration')),
            'view_count': int_or_none(clip.get('playCount')),
            'like_count': int_or_none(clip.get('likeCount')),
            'comment_count': int_or_none(clip.get('commentCount')),
            'formats': formats,
        }


class KakaoPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.kakao\.com/channel/(?P<channel>\d+)/playlist/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://tv.kakao.com/channel/2653401/playlist/12305',
        'info_dict': {
            'id': '12305',
            'title': '아는 형님 1회',
        },
        'params': {
            'skip_download': True
        },
        'playlist_count': 23
    }, {
        'note': 'Video url with playlist',
        'url': 'http://tv.kakao.com/channel/2657529/cliplink/301795620?playlistId=71340&metaObjectType=Playlist',
        'info_dict': {
            'id': '71340',
            'title': '오버워치 단편',
        },
        'params': {
            'skip_download': True
        },
        'playlist_mincount': 90
    }, {
        'note': 'Video url with playlist, but with --no-playlist ',
        'url': 'http://tv.kakao.com/channel/2657529/cliplink/301795620?playlistId=71340&metaObjectType=Playlist',
        'info_dict': {
            'id': '301795620',
            'ext': 'mp4',
            'title': '신영웅 떡밥 자세히 파헤치기',
            'upload_date': '20170224',
            'uploader_id': 2657529,
            'uploader': '게임친구 롤큐',
            'timestamp': 1487936269
        },
        'params': {
            'skip_download': True,
            'noplaylist': True
        }
    }]

    def _real_extract(self, url):
        list_id = self._match_id(url)
        webpage = self._download_webpage(url, list_id)

        try:
            list_name = self._html_search_regex('class="loss_word tit_epiname"\>(.*)', webpage, 'list title')
        except ExtractorError:
            raise ExtractorError('This playlist is empty', expected=True)

        listelement = self._search_regex('(\<ul class="list_vertical" data-playlist-id.*?\<\/ul\>)', webpage, 'lists', flags=re.DOTALL)

        entries = []
        for entry in re.findall(r'<a href="(.*?)\?', listelement, re.DOTALL):
            url = 'http://tv.kakao.com' + entry
            entries.append(self.url_result(url))
        return self.playlist_result(entries, list_id, list_name)


class KakaoChannelIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.kakao\.com/channel/(?P<id>\d+)?/(?!(cliplink|playlist))'

    _TESTS = [{
        'url': 'http://tv.kakao.com/channel/2685195/',
        'info_dict': {
            'id': '2685195',
            'title': 'Mr.아재의 만들기'
        },
        'params': {
            'skip_download': True,
        },
        'playlist_mincount': 250
    }, {
        'note': 'This Channel has over 10k videos',
        'url': 'http://tv.kakao.com/channel/19635/video',
        'info_dict': {
            'id': '19635',
            'title': 'iHQ'
        },
        'params': {
            'skip_download': True,
        },
        'playlist_mincount': 11000
    }]

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        channel_info = self._download_json(
            '%s/channels/%s/' % (KakaoIE._API_BASE, channel_id),
            channel_id,
            note='Downloading channel info',
        )
        channel_name = channel_info.get('name')
        channel_description = channel_info.get('description')
        query = {
            'sort': 'CreateTime',
            'fulllevels': 'clipLinkList,liveLinkList',
            'fields': 'ccuCount,thumbnailUri,-user,-clipChapterThumbnailList,-tagList',
            'size': '200',
            'page': 1
        }
        hasmore = True
        entries = []
        while hasmore:
            videolist = self._download_json(
                '%s/channels/%s/videolinks' % (KakaoIE._API_BASE, channel_id),
                channel_id,
                note='Downloading video list %s' % query.get('page'),
                query=query
            )
            hasmore = videolist.get('hasMore')
            query['page'] += 1
            for clip in videolist.get('clipLinkList'):
                entries.append(self.url_result('http://tv.kakao.com/v/%s' % clip.get('id')))

        return self.playlist_result(
            entries,
            channel_id,
            channel_name,
            channel_description)
