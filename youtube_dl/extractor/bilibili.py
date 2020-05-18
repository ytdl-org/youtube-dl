# coding: utf-8
from __future__ import unicode_literals

import hashlib
import re
from datetime import datetime

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    str_or_none,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                      (?:www\.)bilibili.(?:com|tv)
                      /video/[aAbB][vV](?P<id>[^/?#&]+)
                    '''

    _TESTS = [{
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '5f7d29e1a2872f3df0cf76b1f87d3788',
        'info_dict': {
            'id': '1074402',
            'ext': 'flv',
            'title': '【金坷垃】金泡沫',
            'description': 'md5:ce18c2a2d2193f0df2917d270f2e5923',
            'duration': 308.067,
            'timestamp': 1397983878,
            'upload_date': '20140420',
            'thumbnail': r're:^https?://.+\.jpg',
            'uploader': '菊子桑',
            'uploader_id': '156160',
        },
    }, {
        # Title with double quotes
        'url': 'http://www.bilibili.com/video/av8903802/',
        'info_dict': {
            'id': '8903802',
            'title': '阿滴英文｜英文歌分享#6 "Closer',
            'description': '滴妹今天唱Closer給你聽! 有史以来，被推最多次也是最久的歌曲，其实歌词跟我原本想像差蛮多的，不过还是好听！ 微博@阿滴英文',
            'uploader': '阿滴英文',
            'uploader_id': '65880958',
            'upload_date': '20170301',
            'timestamp': 1488353834,
        },
        'params': {
            'skip_download': True,  # Test metadata only
        },
        'playlist': [{
            'info_dict': {
                'id': '8903802_14694589_1',
                'ext': 'flv',
                'title': '阿滴英文｜英文歌分享#6 "Closer',

            },
            'params': {
                'skip_download': True,  # Test metadata only
            },
        }, {
            'info_dict': {
                'id': '8903802_14694589_2',
                'ext': 'flv',
                'title': '阿滴英文｜英文歌分享#6 "Closer',
            },
            'params': {
                'skip_download': True,  # Test metadata only
            },
        }]
    }, {
        # new BV video id format
        'url': 'https://www.bilibili.com/video/BV1JE411F741',
        'only_matching': True,
    }, {
        # multiple part video
        'url': 'https://www.bilibili.com/video/BV1FJ411k7q9',
        'info_dict': {
            'id': '1FJ411k7q9',
            'title': '【原始技术】用草木灰代替粘土（Minecraft真人版第五十一弹）',
            'description': '【Primitive Technology@Youtube】\n看着上一集烧砖产生的大量草木灰，小哥有了新想法：草木灰也许可以作为粘土的又一种替代品，用来做罐子、砖块都行，不怕浸水，还不需要烧制。这是小哥第51个视频，完整合集见av2920827。更多细节见: https://youtu.be/rG6nzrksbPQ，想帮小哥制作更好的视频可以上Patreon给小哥充电：https://www.patreon.com/user?u=2945881',
            'uploader': '昨梦电羊',
            'uploader_id': '1388774',
            'upload_date': '20191215',
            'timestamp': 1576376056,
        },
        'params': {
            'skip_download': True,  # Test metadata only
        },
        'playlist': [{
            'info_dict': {
                'id': '1FJ411k7q9_135730700_1',
                'ext': 'flv',
                'title': '字幕版1080p',

            },
            'params': {
                'skip_download': True,  # Test metadata only
            },
        }, {
            'info_dict': {
                'id': '1FJ411k7q9_135730766_1',
                'ext': 'flv',
                'title': '无字幕版',
            },
            'params': {
                'skip_download': True,  # Test metadata only
            },
        }]
    }
    ]

    _APP_KEY = 'iVGUTjsxvpLeuDCf'
    _BILIBILI_KEY = 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'

    def _report_error(self, result):
        if 'message' in result:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, result['message']), expected=True)
        elif 'code' in result:
            raise ExtractorError('%s returns error %d' % (self.IE_NAME, result['code']), expected=True)
        else:
            raise ExtractorError('Can\'t extract Bangumi episode ID')

    def _aid_to_bid(self, aid):
        '''
        convert bilibili avid to bid
        '''

        api_url = 'http://api.bilibili.com/x/web-interface/view?aid=%s' % (aid, )
        js = self._download_json(api_url, aid, 'convert avid to bv id', 'convert failed')
        return js['data']['bvid']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # save the origin video id
        original_video_id = video_id
        webpage = self._download_webpage(url, video_id)
        title = ''
        timestamp = 0
        thumbnail = ''
        description = ''
        uploader_id = ''
        uploader_name = ''
        view_count = 0
        part_list = []
        upload_date = ''
        # normal video
        if re.match(r'^\d+$', video_id):
            video_id = self._aid_to_bid(video_id)
            self.to_screen("%s: convert to bvid %s" % (original_video_id, video_id))
        list_api_url = 'https://api.bilibili.com/x/web-interface/view/detail?bvid=%s' % (video_id, )
        js = self._download_json(list_api_url, original_video_id, 'downloading video list', 'downloding video list failed', fatal=False)['data']
        video_list = js['View']['pages']
        title = js['View']['title']
        thumbnail = js.get('View', {}).get('pic')
        description = js.get('View', {}).get('desc')
        view_count = js.get('View', {}).get('stat', {}).get('view')
        uploader_id = js.get('Card', {}).get('card', {}).get('mid')
        uploader_name = js.get('Card', {}).get('card', {}).get('name')
        self.to_screen("%s: video count: %d" % (original_video_id, len(video_list)))
        part_list = [{'cid': x['cid'], 'title': x['part']} for x in video_list]
        headers = {
            'Referer': url
        }
        headers.update(self.geo_verification_headers())

        entries = []

        RENDITIONS = ('qn=80&quality=80&type=', 'quality=2&type=mp4')
        for part_info in part_list:
            # try to get video playback url, use
            for num, rendition in enumerate(RENDITIONS, start=1):
                payload = 'appkey=%s&cid=%s&otype=json&%s' % (self._APP_KEY, part_info['cid'], rendition)
                sign = hashlib.md5((payload + self._BILIBILI_KEY).encode('utf-8')).hexdigest()

                video_info = self._download_json(
                    'http://interface.bilibili.com/v2/playurl?%s&sign=%s' % (payload, sign),
                    original_video_id, note='Downloading video info for cid: %s' % (part_info['cid'], ),
                    headers=headers, fatal=num == len(RENDITIONS))

                if not video_info:
                    continue

                if 'durl' not in video_info:
                    if num < len(RENDITIONS):
                        continue
                    self._report_error(video_info)
                part_title = part_info['title']
                if len(part_list) == 1:
                    # if video only got one part, use video title instead of part title
                    part_title = title
                for idx, durl in enumerate(video_info['durl'], start=1):
                    # some video is splited to many fragments, here is this fragments
                    formats = [{
                        'url': durl['url'],
                        'filesize': int_or_none(durl['size']),
                    }]
                    for backup_url in durl.get('backup_url', []):
                        formats.append({
                            'url': backup_url,
                            # backup URLs have lower priorities
                            'preference': -2 if 'hd.mp4' in backup_url else -3,
                        })

                    for a_format in formats:
                        a_format.setdefault('http_headers', {}).update({
                            'Referer': url,
                        })

                    self._sort_formats(formats)

                    entries.append({
                        'id': '%s_%s_%s' % (original_video_id, part_info['cid'], idx),
                        'duration': float_or_none(durl.get('length'), 1000),
                        'formats': formats,
                        'title': part_title
                    })
                break
        if not title:
            title = self._html_search_regex(
                ('<h1[^>]+\btitle=(["\'])(?P<title>(?:(?!\1).)+)\1',
                 '(?s)<h1[^>]*>(?P<title>.+?)</h1>'), webpage, 'title',
                group='title', fatal=False)
        if not timestamp:
            timestamp = self._html_search_regex(
                (r'"pubdate":(?P<timestamp>\d+),'), webpage, 'timestamp',
                group='timestamp', fatal=False)
        if not uploader_id or not uploader_name:
            uploader_id = self._html_search_regex(
                r'<a[^>]+href="(?:https?:)?//space\.bilibili\.com/\d+"[^>]*>(?P<name>[^<]+)',
                webpage, 'id',
                group='id', fatal=False)
            uploader_name = self._html_search_regex(
                r'<a[^>]+href="(?:https?:)?//space\.bilibili\.com/(?P<id>\d+)"',
                webpage, 'name',
                group='name', fatal=False)
        if not thumbnail:
            thumbnail = self._html_search_meta(['og:image', 'thumbnailUrl'], webpage, fatal=False)
        if not description:
            description = self._html_search_meta('description', webpage, fatal=False)
        if timestamp:
            timestamp = int_or_none(timestamp)
            upload_date = datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
        if view_count:
            view_count = int_or_none(view_count)
        if len(entries) == 1:
            entry = entries[0]
            entry['uploader'] = uploader_name
            entry['uploader_id'] = uploader_id
            entry['id'] = original_video_id
            entry['title'] = title
            entry['description'] = description
            entry['timestamp'] = timestamp
            entry['thumbnail'] = thumbnail
            entry['upload_date'] = upload_date
            entry['view_count'] = view_count
            return entry
        else:
            playlist_entry = self.playlist_result(entries, id, title, description)
            playlist_entry['uploader'] = uploader_name
            playlist_entry['uploader_id'] = uploader_id
            playlist_entry['timestamp'] = timestamp
            playlist_entry['thumbnail'] = thumbnail
            playlist_entry['upload_date'] = upload_date
            playlist_entry['view_count'] = view_count
            return playlist_entry


class BiliBiliBangumiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)bilibili.com/bangumi/media/[mD][dD](?P<id>\d+)'

    IE_NAME = 'bangumi.bilibili.com'
    IE_DESC = 'BiliBili番剧'

    _TESTS = [{
        'url': 'https://www.bilibili.com/bangumi/media/md3814',
        'info_dict': {
            'id': '3814',
            'title': '魔动王 最后的魔法大战',
            'description': 'md5:9634eb0d85d515f6930fa1c833ccee63',
        },
        'playlist': [{
            'info_dict': {
                'id': '3814_1_1',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_2',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_3',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_4',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_5',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_2_1',
                'ext': 'flv',
                'title': '最后的魔法大战 后篇'
            },
        }
        ]
    }]

    def _real_extract(self, url):
        headers = {
            'Referer': url
        }
        bangumi_id = self._match_id(url)
        bangumi_info = self._download_json(
            'https://api.bilibili.com/pgc/view/web/season?season_id=%s' % (bangumi_id,),
            bangumi_id,
            'Downloading bangumi info',
            'Downloading bangumi failed')['result']
        title = bangumi_info['season_title']
        description = bangumi_info.get('evaluate')
        episodes = bangumi_info.get('episodes')
        self.to_screen('%s: episode count: %d' % (bangumi_id, len(episodes)))
        entries = []
        for idx, episode in enumerate(episodes, start=1):
            play_back_info = self._download_json(
                'http://api.bilibili.com/x/player/playurl?bvid=%s&cid=%s&qn=80' % (episode['bvid'], episode['cid']),
                bangumi_id,
                'downloding playback info for ep: %d' % (idx, ),
                headers=headers)['data']
            for fragment_idx, durl in enumerate(play_back_info['durl'], start=1):
                # some video is splited to many fragments, here is this fragments
                formats = [{
                    'url': durl['url'],
                    'filesize': int_or_none(durl.get('size')),
                }]
                for backup_url in durl.get('backup_url', []):
                    formats.append({
                        'url': backup_url,
                        # backup URLs have lower priorities
                        'preference': -2 if 'hd.mp4' in backup_url else -3,
                    })

                for a_format in formats:
                    a_format.setdefault('http_headers', {}).update({
                        'Referer': url,
                    })

                self._sort_formats(formats)
                entries.append({
                    'id': '%s_%d_%d' % (bangumi_id, idx, fragment_idx),
                    'duration': float_or_none(durl.get('length'), 1000),
                    'formats': formats,
                    'title': episode.get('long_title', '')
                })
        return self.playlist_result(entries, bangumi_id, title, description)


class BiliBiliBangumiEpisodeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)bilibili.com/bangumi/play/[eE][pP](?P<id>\d+)'

    IE_NAME = 'bangumi.bilibili.com'
    IE_DESC = 'BiliBili番剧'
    _TESTS = [{
        'url': 'https://www.bilibili.com/bangumi/play/ep86635',
        'info_dict': {
            'id': '3814',
            'title': '魔动王 最后的魔法大战',
            'description': 'md5:9634eb0d85d515f6930fa1c833ccee63',
        },
        'playlist': [{
            'info_dict': {
                'id': '3814_1_1',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_2',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_3',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_4',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_1_5',
                'ext': 'flv',
                'title': '最后的魔法大战 前篇'
            },
        }, {
            'info_dict': {
                'id': '3814_2_1',
                'ext': 'flv',
                'title': '最后的魔法大战 后篇'
            },
        }
        ]
    }]

    def _real_extract(self, url):
        ep_id = self._match_id(url)
        bangumi_id = self._download_json('https://api.bilibili.com/pgc/view/web/season?ep_id=%s' % (ep_id, ), ep_id, 'Downloading bangumi info')['result']['media_id']
        return self.url_result(
            'https://www.bilibili.com/bangumi/media/md%s' % bangumi_id,
            ie=BiliBiliBangumiIE.ie_key(), video_id=ep_id)


class BilibiliAudioBaseIE(InfoExtractor):
    def _call_api(self, path, sid, query=None):
        if not query:
            query = {'sid': sid}
        return self._download_json(
            'https://www.bilibili.com/audio/music-service-c/web/' + path,
            sid, query=query)['data']


class BilibiliAudioIE(BilibiliAudioBaseIE):
    _VALID_URL = r'https?://(?:www\.)?bilibili\.com/audio/au(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.bilibili.com/audio/au1003142',
        'md5': 'fec4987014ec94ef9e666d4d158ad03b',
        'info_dict': {
            'id': '1003142',
            'ext': 'm4a',
            'title': '【tsukimi】YELLOW / 神山羊',
            'artist': 'tsukimi',
            'comment_count': int,
            'description': 'YELLOW的mp3版！',
            'duration': 183,
            'subtitles': {
                'origin': [{
                    'ext': 'lrc',
                }],
            },
            'thumbnail': r're:^https?://.+\.jpg',
            'timestamp': 1564836614,
            'upload_date': '20190803',
            'uploader': 'tsukimi-つきみぐー',
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        au_id = self._match_id(url)

        play_data = self._call_api('url', au_id)
        formats = [{
            'url': play_data['cdns'][0],
            'filesize': int_or_none(play_data.get('size')),
        }]

        song = self._call_api('song/info', au_id)
        title = song['title']
        statistic = song.get('statistic') or {}

        subtitles = None
        lyric = song.get('lyric')
        if lyric:
            subtitles = {
                'origin': [{
                    'url': lyric,
                }]
            }

        return {
            'id': au_id,
            'title': title,
            'formats': formats,
            'artist': song.get('author'),
            'comment_count': int_or_none(statistic.get('comment')),
            'description': song.get('intro'),
            'duration': int_or_none(song.get('duration')),
            'subtitles': subtitles,
            'thumbnail': song.get('cover'),
            'timestamp': int_or_none(song.get('passtime')),
            'uploader': song.get('uname'),
            'view_count': int_or_none(statistic.get('play')),
        }


class BilibiliAudioAlbumIE(BilibiliAudioBaseIE):
    _VALID_URL = r'https?://(?:www\.)?bilibili\.com/audio/am(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.bilibili.com/audio/am10624',
        'info_dict': {
            'id': '10624',
            'title': '每日新曲推荐（每日11:00更新）',
            'description': '每天11:00更新，为你推送最新音乐',
        },
        'playlist_count': 20,
    }

    def _real_extract(self, url):
        am_id = self._match_id(url)

        songs = self._call_api(
            'song/of-menu', am_id, {'sid': am_id, 'pn': 1, 'ps': 100})['data']

        entries = []
        for song in songs:
            sid = str_or_none(song.get('id'))
            if not sid:
                continue
            entries.append(self.url_result(
                'https://www.bilibili.com/audio/au' + sid,
                BilibiliAudioIE.ie_key(), sid))

        if entries:
            album_data = self._call_api('menu/info', am_id) or {}
            album_title = album_data.get('title')
            if album_title:
                for entry in entries:
                    entry['album'] = album_title
                return self.playlist_result(
                    entries, am_id, album_title, album_data.get('intro'))

        return self.playlist_result(entries, am_id)


class BiliBiliPlayerIE(InfoExtractor):
    _VALID_URL = r'https?://player\.bilibili\.com/player\.html\?.*?\baid=(?P<id>\d+)'
    _TEST = {
        'url': 'http://player.bilibili.com/player.html?aid=92494333&cid=157926707&page=1',
        'only_matching': True,
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.url_result(
            'http://www.bilibili.tv/video/av%s/' % video_id,
            ie=BiliBiliIE.ie_key(), video_id=video_id)
