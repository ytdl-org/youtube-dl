# coding: utf-8
from __future__ import unicode_literals
import ast
from bs4 import BeautifulSoup
import json
from .common import InfoExtractor
from ..utils import (
    compat_str,
    ExtractorError,
    int_or_none,
    str_or_none,
    try_get,
    url_or_none)


class TikTokBaseIE(InfoExtractor):
    def _extract_aweme(self, data):
        video = data['video']
        description = str_or_none(try_get(data, lambda x: x['desc']))
        width = int_or_none(try_get(data, lambda x: video['width']))
        height = int_or_none(try_get(data, lambda x: video['height']))

        format_urls = set()
        formats = []
        for format_id in (
                'play_addr_lowbr', 'play_addr', 'play_addr_h264',
                'download_addr'):
            for format in try_get(
                    video, lambda x: x[format_id]['url_list'], list) or []:
                format_url = url_or_none(format)
                if not format_url:
                    continue
                if format_url in format_urls:
                    continue
                format_urls.add(format_url)
                formats.append({
                    'url': format_url,
                    'ext': 'mp4',
                    'height': height,
                    'width': width,
                })
        self._sort_formats(formats)

        thumbnail = url_or_none(try_get(
            video, lambda x: x['cover']['url_list'][0], compat_str))
        uploader = try_get(data, lambda x: x['author']['nickname'], compat_str)
        timestamp = int_or_none(data.get('create_time'))
        comment_count = int_or_none(data.get('comment_count')) or int_or_none(
            try_get(data, lambda x: x['statistics']['comment_count']))
        repost_count = int_or_none(try_get(
            data, lambda x: x['statistics']['share_count']))

        aweme_id = data['aweme_id']

        return {
            'id': aweme_id,
            'title': uploader or aweme_id,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'timestamp': timestamp,
            'comment_count': comment_count,
            'repost_count': repost_count,
            'formats': formats,
        }


class TikTokIE(TikTokBaseIE):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:
                                (?:m\.)?tiktok\.com/v|
                                (?:www\.)?tiktok\.com/share/video|
                                (?:www\.|)tiktok\.com\/@(?:.*?)\/video
                            )
                            /(?P<id>\d+)
                    '''
    _TESTS = [{
        'url': 'https://m.tiktok.com/v/6606727368545406213.html',
        'md5': 'd584b572e92fcd48888051f238022420',
        'info_dict': {
            'id': '6606727368545406213',
            'ext': 'mp4',
            'title': 'Zureeal',
            'description': '#bowsette#mario#cosplay#uk#lgbt#gaming#asian#bowsettecosplay',
            'thumbnail': r're:^https?://.*~noop.image',
            'uploader': 'Zureeal',
            'timestamp': 1538248586,
            'upload_date': '20180929',
            'comment_count': int,
            'repost_count': int,
        }
    }, {
        'url': 'https://www.tiktok.com/share/video/6606727368545406213',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_api = self._download_json('https://www.tiktok.com/oembed?url=' + url, video_id)

        webpage = self._download_webpage(url, video_id)
        soup = BeautifulSoup(webpage, features="html.parser")
        json_next_data = soup.find(id='__NEXT_DATA__')
        props = json_next_data.contents[0]
        json_data_encode = json.dumps(props.encode('utf-8'))
        ast_le = ast.literal_eval(json_data_encode)
        data_dict = json.loads(ast_le)

        item_info = data_dict['props']['pageProps']['videoData']['itemInfos']
        timestamp = int(item_info['createTime'])
        shares = item_info['shareCount']
        views = item_info['playCount']
        duration = item_info['video']['videoMeta']['duration']
        provider_id = item_info['authorId']
        comments_count = item_info['commentCount']
        likes_count = item_info['diggCount']

        return self.info_dict(video_id, str(url), json_api['title'],
                              json_api['author_name'], timestamp, json_api['thumbnail_url'],
                              views, provider_id, False, 'not_live', likes_count, shares, '', comments_count, duration)

    def info_dict(self, video_id, url, video_title,
                  uploader, timestamp, thumbnail,
                  view_count, uploader_id, is_live, live_status
                  , likes_count, shares_count, subtitles, comment_count, duration):
        info_dict = {
            'id': video_id,
            'url': url,
            'title': video_title,
            'uploader': uploader,
            'timestamp': timestamp,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'uploader_id': uploader_id,
            'is_live': is_live,
            'live_status': live_status,
            'like_count': likes_count,
            'share_count': shares_count,
            'subtitles': subtitles,
            'comment_count': comment_count,
            'duration': duration,
            'ext':'mp.4'

        }
        return info_dict


class TikTokUserIE(TikTokBaseIE):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:
                                (?:m\.)?tiktok\.com/h5/share/usr|
                                (?:www\.)?tiktok\.com/share/user
                            )
                            /(?P<id>\d+)
                    '''
    _TESTS = [{
        'url': 'https://m.tiktok.com/h5/share/usr/188294915489964032.html',
        'info_dict': {
            'id': '188294915489964032',
        },
        'playlist_mincount': 24,
    }, {
        'url': 'https://www.tiktok.com/share/user/188294915489964032',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        user_id = self._match_id(url)
        data = self._download_json(
            'https://m.tiktok.com/h5/share/usr/list/%s/' % user_id, user_id,
            query={'_signature': '_'})
        entries = []
        for aweme in data['aweme_list']:
            try:
                entry = self._extract_aweme(aweme)
            except ExtractorError:
                continue
            entry['extractor_key'] = TikTokIE.ie_key()
            entries.append(entry)
        return self.playlist_result(entries, user_id)
