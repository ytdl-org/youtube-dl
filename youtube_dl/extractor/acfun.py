# coding: utf-8
from __future__ import unicode_literals

import base64
import functools
import json
import re
import time

from .common import (
    InfoExtractor,
)
from ..compat import (
    compat_ord,
    compat_parse_qs,
    compat_str,
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    OnDemandPagedList,
    dict_get,
    float_or_none,
    int_or_none,
)


_ACFUN_HOST = r'''
    (?x)^(
        (?:https?://|//)
        (?:www\.)?acfun\.
        (?:cn|tv|com|tudou\.com)
    )'''


class _AcFunBaseIE(InfoExtractor):
    # api limit, max 20
    _PAGE_SIZE = 20

    def _acfun_api_raw(self, video_id, url, args, kw, code, msg, data, succ):
        headers = kw.pop('headers', {})
        headers['deviceType'] = 1
        kw['headers'] = headers
        json_data = self._download_json(url, video_id, *args, **kw)
        if succ != json_data[code]:
            raise ExtractorError(json_data[msg], expected=True, video_id=video_id)
        return json_data[data]

    def _acfun_api_v0(self, video_id, url, *args, **kw):
        return self._acfun_api_raw(video_id, url, args, kw, 'status', 'msg', 'data', 200)

    def _acfun_api_v1(self, video_id, url, *args, **kw):
        return self._acfun_api_raw(video_id, url, args, kw, 'code', 'message', 'data', 200)

    def _acfun_api_v2(self, video_id, url, *args, **kw):
        return self._acfun_api_raw(video_id, url, args, kw, 'errorid', 'errordesc', 'vdata', 0)

    @classmethod
    def _match_two(cls, url, group):
        match = re.match(cls._VALID_URL, url)
        video_id = compat_str(match.group('id'))
        second = int_or_none(match.group(group))
        return video_id, second

    @classmethod
    def _get_desc(cls, info):
        return dict_get(info, ['description', 'intro'])


class AcFunVideoIE(_AcFunBaseIE):
    IE_NAME = 'acfun:video'
    IE_DESC = False  # Do not list
    # NOTE: require query string, internal use only
    _VALID_URL = _ACFUN_HOST + r'/v/(?P<id>a[bc]\d+_\d+)\?(?P<query>.*)$'
    # note some urls for different sourceType
    _TESTS = [] and [{
        'url': 'http://www.acfun.cn/v/ab1470310_1',
        'note': 'sourceType: youku',
        'info_dict': {
            '_type': 'url',
            'id': 'XMTI3ODI4OTU1Ng==',
            'title': '【七月】悠哉日常大王Repeat_第1话',
            'url': 'https://v.youku.com/v_show/id_XMTI3ODI4OTU1Ng==.html',
        },
    }, {
        'url': 'http://www.acfun.cn/v/ab1464837_1',
        'note': 'sourceType: youku2',
        'info_dict': {
            'id': 'XNzk4NzQzMzI4',
            'title': '晨曦公主_第1话',
            'url': 'https://v.youku.com/v_show/id_XNzk4NzQzMzI4.html',
        },
    }, {
        'url': 'http://www.acfun.cn/v/ab1464814_1',
        'note': 'sourceType: iqiyi',
        'info_dict': {
            'id': '7f3791481e31a308c43d2f129c584ded:319095200',
            'title': '白箱 SHIROBAKO_第1话',
        },
        'skip': 'TODO: how to build url?',
    }, {
        'url': 'http://www.acfun.cn/v/ab1464842_1',
        'note': 'sourceType: qq2',
        'info_dict': {
            'id': 'k0015myyz8t',
            'title': '【十月】大图书馆的牧羊人_第1话',
            'url': 'https://v.qq.com/x/page/k0015myyz8t.html',
        },
    }, {
        'url': 'http://www.acfun.cn/v/ab1103_1',
        'note': 'sourceType: letv2',
        'info_dict': {
            'id': '20055264',
            'title': '乒乓_第1话',
            'url': 'http://www.le.com/ptv/vplay/20055264.html',
        },
    }, {
        'url': 'http://www.acfun.cn/v/ab1470224_1',
        'note': 'sourceType: pptv',
        'info_dict': {
            'id': 'V2GFAmrQQH7hX6M',
            'title': '【四月】关于完全听不懂老公在说什么的事 第二季_第1话',
            'url': 'http://v.pptv.com/show/V2GFAmrQQH7hX6M.html',
        },
    }]

    # copied from youku.py (function removed in commit 59ed87c)
    @classmethod
    def _yk_t(cls, s1, s2):
        ls = list(range(256))
        t = 0
        for i in range(256):
            t = (t + ls[i] + compat_ord(s1[i % len(s1)])) % 256
            ls[i], ls[t] = ls[t], ls[i]
        s = bytearray()
        x, y = 0, 0
        for i in range(len(s2)):
            y = (y + 1) % 256
            x = (x + ls[y]) % 256
            ls[x], ls[y] = ls[y], ls[x]
            s.append(compat_ord(s2[i]) ^ ls[(ls[x] + ls[y]) % 256])
        return bytes(s)

    def _acfun_flash_data(self, vid, sign, ref, video_id):
        api = 'http://player.acfun.cn/flash_data?vid={vid}&ct=85&ev=3&sign={sign}&time={time}'
        flash_data = self._download_json(
            api.format(vid=vid, sign=sign, time=int(time.time() * 1000)),
            video_id, note=False, headers={'Referer': ref})
        encrypted = base64.b64decode(flash_data['data'])
        decrypted = self._yk_t('8bdc7e1a', encrypted)
        return json.loads(decrypted.decode('utf8'))

    def _acfun_video(self, vid, url, title, video_id):
        info = self._download_json(
            'http://www.acfun.cn/video/getVideo.aspx?id={}'.format(vid),
            video_id, note='Downloading video part info: id=%s' % vid)
        if not info['success']:
            raise ExtractorError(info['result'], expected=True, video_id=video_id)
        sourceType = info['sourceType']
        if 'zhuzhan' == sourceType:
            return self._acfun_video_zhuzhan(vid, info, url, title, video_id)
        sourceId = info['sourceId']
        new_url = None
        if sourceType in ('youku', 'youku2'):
            new_url = 'https://v.youku.com/v_show/id_{}.html'.format(sourceId)
        elif sourceType in ('qq', 'qq2'):
            new_url = 'https://v.qq.com/x/page/{}.html'.format(sourceId)
        elif sourceType in ('letv', 'letv2'):
            new_url = 'http://www.le.com/ptv/vplay/{}.html'.format(sourceId)
        elif sourceType in ('pptv'):
            sourceId = sourceId.split(':')[1]
            new_url = 'http://v.pptv.com/show/{}.html'.format(sourceId)
        if new_url:
            return self.url_result(new_url, video_id=sourceId, video_title=title)
        raise ExtractorError('unsupported sourceType: %s' % sourceType, expected=True, video_id=video_id)

    def _acfun_video_zhuzhan(self, vid, info, url, title, video_id):
        flash = self._acfun_flash_data(info['sourceId'], info['encode'], url, video_id)
        streams = [stream for stream in flash['stream'] if 'segs' in stream]
        streams.sort(key=lambda v: int(v['width']))
        segs_len = [len(stream['segs']) for stream in streams]
        same_len = 1 == len(set(segs_len))
        entries = []
        for idx in range(max(segs_len)):
            formats = [{
                'url': stream['segs'][idx]['url'],
                'ext': 'mp4',
                'format_id': stream['stream_type'],
                'width': int_or_none(stream['width']),
                'height': int_or_none(stream['height']),
                'filesize': stream['segs'][idx]['size'],
            } for sidx, stream in enumerate(streams) if idx < segs_len[sidx]]
            seconds = streams[0]['segs'][idx]['seconds'] if same_len else None
            entries.append({
                'id': 'av%s_seg%d' % (vid, idx),
                'title': title,
                'formats': formats,
                'duration': float_or_none(seconds),
            })
        return {
            '_type': 'multi_video',
            'id': video_id,
            'entries': entries,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        parsed_url = compat_urllib_parse_urlparse(url)
        query = compat_parse_qs(parsed_url.query)
        title = query['title'][0] if 'title' in query else video_id
        vid = query['vid'][0]
        return self._acfun_video(vid, url, title, video_id)


class _AcFunVideoListIE(_AcFunBaseIE):
    def _acfun_list(self, videos_info, video_id, video_idx):
        info = {
            'description': self._get_desc(videos_info),
            'thumbnail': videos_info.get('cover'),
            'tags': videos_info.get('tags'),
            'timestamp': int_or_none(videos_info.get('releaseDate'), scale=1000)
        }
        if 'visit' in videos_info:
            visit = videos_info['visit']
            info.update({
                'view_count': visit['views'],
                'comment_count': visit['comments'],
            })
        if 'owner' in videos_info:
            owner = videos_info['owner']
            info.update({
                'uploader': owner['name'],
                'uploader_id': owner['id'],
                'uploader_url': 'http://www.acfun.cn/u/%d.aspx' % owner['id'],
            })

        entries = []
        for idx, video in enumerate(videos_info['videos']):
            url = 'http://www.acfun.cn/v/%s_%d' % (video_id, idx + 1)
            title = '%s_%s' % (videos_info['title'], video['title'])
            if 'ac' == video_id[:2] and 1 == len(videos_info['videos']):
                title = videos_info['title']
            vid = dict_get(video, ['videoId', 'id'])
            query_str = compat_urllib_parse_urlencode({
                'title': title,
                'vid': vid,
            })
            entry = {
                '_type': 'url_transparent',
                'url': '%s?%s' % (url, query_str),
                'ie_key': AcFunVideoIE.ie_key(),
                'title': title,
            }
            entry.update(info)
            if 'updateTime' in video:
                entry['timestamp'] = int_or_none(video['updateTime'], scale=1000)
            entries.append(entry)

        if 1 == len(entries):
            video_idx = 1
        if video_idx is not None:
            return entries[video_idx - 1]

        return self.playlist_result(
            entries, video_id,
            videos_info['title'], self._get_desc(videos_info))


class AcFunIE(_AcFunVideoListIE):
    IE_NAME = 'acfun'
    IE_DESC = 'AcFun 弹幕视频网'
    _VALID_URL = _ACFUN_HOST + r'/v/(?P<id>ac\d+)(?:_(?P<idx>\d+))?'
    _TESTS = [{
        'url': 'http://www.acfun.cn/v/ac3704490',
        'playlist_mincount': 23,
        'info_dict': {
            'id': 'ac3704490',
            'title': '广西车神叛逆少年之夺命125合集（搬运）',
            'description': 'md5:4c8bdbc6a8217b8a95c27671f3e6a597',
        },
    }, {
        'url': 'http://www.acfun.cn/v/ac3913858_1',
        'info_dict': {
            'id': 'ac3913858_1',
            'title': '中国交通事故合集20170811：每天10分钟最新国内车祸实例，助你提高安全意识',
            'description': 'md5:0cbb9578cb5383d5bc75bfff4984b040',
            'timestamp': 1502543900,
            'uploader_id': 4075269,
            'uploader': '交通事故video',
        },
        'playlist': [{
            'info_dict': {
                'id': 'av5500038_seg0',
                'ext': 'mp4',
                'title': 'md5:7f843db80b5769311d04622846e71b59',
                'format_id': 'mp4hd2',
                'duration': 189,
            },
        }, {
            'info_dict': {
                'id': 'av5500038_seg1',
                'ext': 'mp4',
                'title': 'md5:7f843db80b5769311d04622846e71b59',
                'format_id': 'mp4hd2',
                'duration': 178,
            },
        }, {
            'info_dict': {
                'id': 'av5500038_seg2',
                'ext': 'mp4',
                'title': 'md5:7f843db80b5769311d04622846e71b59',
                'format_id': 'mp4hd2',
                'duration': 177,
            },
        }, {
            'info_dict': {
                'id': 'av5500038_seg3',
                'ext': 'mp4',
                'title': 'md5:7f843db80b5769311d04622846e71b59',
                'format_id': 'mp4hd2',
                'duration': 118,
            },
        }],
        'params': {
            'skip_download': True,
        },
    }]

    def _acfun_video_info(self, video_id):
        return self._acfun_api_v2(
            video_id, 'http://apipc.app.acfun.cn/v2/videos/' + video_id[2:],
            note='Downloading video info')

    def _real_extract(self, url):
        video_id, video_idx = self._match_two(url, 'idx')
        videos_info = self._acfun_video_info(video_id)
        return self._acfun_list(videos_info, video_id, video_idx)


class AcFunBangumiIE(_AcFunVideoListIE):
    IE_NAME = 'acfun:bangumi'
    IE_DESC = 'AcFun - 番剧'
    _VALID_URL = _ACFUN_HOST + r'/v/(?P<id>ab\d+)(?:_(?P<idx>\d+))?'
    _TESTS = [{
        'url': 'http://www.acfun.cn/v/ab1480054',
        'playlist_count': 12,
        'info_dict': {
            'id': 'ab1480054',
            'title': '四叠半神话大系',
            'description': 'md5:9d03a432ba6e84a3155727e36ed5f16a',
        },
    }, {
        'url': 'http://www.acfun.cn/v/ab1470396_1',
        'info_dict': {
            'id': 'ab1470396_1',
            'title': '【十月】无论如何都想加入生肖【AcFun独家正版】_第1话',
            'description': 'md5:74f7029bb5615a3efe52f4bef9388d65',
        },
        'playlist': [{
            'info_dict': {
                'id': 'av2766142_seg0',
                'ext': 'mp4',
                'title': 'md5:922e303fe6e6f21623d3ca72f6b6429f',
                'format_id': 'mp4hd',
                'duration': 359,
            },
        }],
        'params': {
            'skip_download': True,
        },
    }]

    def _acfun_bangumi_page(self, bangumi_id, pagesize, pagenum):
        page = pagenum + 1
        query = {
            'bangumiId': bangumi_id[2:],
            'pageSize': pagesize,
            'pageNo': page,
            'isWeb': 1,
            'order': 2,
        }
        info = self._acfun_api_v0(
            bangumi_id, 'http://www.acfun.cn/bangumi/video/page',
            query=query,
            note='Downloading Bangumi video info, page=%d' % page)
        return info['list']

    def _acfun_bangumi_info(self, bangumi_id):
        bangumi_info = self._acfun_api_v2(
            bangumi_id, 'http://apipc.app.acfun.cn/v2/bangumis/' + bangumi_id[2:],
            query={'page': '{num:%d,size:%d}' % (1, self._PAGE_SIZE)},
            note='Downloading Bangumi info')
        if 'tags' in bangumi_info:
            tags = bangumi_info.pop('tags')
            bangumi_info['tags'] = [tag['name'] for tag in tags]
        return bangumi_info

    def _real_extract(self, url):
        bangumi_id, bangumi_idx = self._match_two(url, 'idx')
        bangumi_info = self._acfun_bangumi_info(bangumi_id)
        paged = OnDemandPagedList(
            functools.partial(self._acfun_bangumi_page, bangumi_id, self._PAGE_SIZE),
            self._PAGE_SIZE)
        bangumi_info['videos'] = paged.getslice()
        return self._acfun_list(bangumi_info, bangumi_id, bangumi_idx)


class _AcFunListIE(_AcFunBaseIE):
    def _acfun_entry(self, video):
        return self.url_result(
            'http://www.acfun.cn/v/ac%s' % video['contentId'],
            ie=AcFunIE.ie_key(),
            video_title=dict_get(video, ['title', 'subtitle']),
        )

    def _acfun_list(self, videos_info, video_id, entries):
        return self.playlist_result(
            entries, video_id,
            videos_info.get('title'), self._get_desc(videos_info))


class AcFunUserIE(_AcFunListIE):
    IE_NAME = 'acfun:user'
    IE_DESC = 'AcFun - UP主投稿'
    _VALID_URL = _ACFUN_HOST + r'/u/(?P<id>\d+)\.aspx'
    _TESTS = [{
        'url': 'http://www.acfun.cn/u/90274.aspx',
        'playlist_mincount': 66,
        'info_dict': {
            'id': '90274',
            'title': '极品国产',
            'description': 'md5:e9b7ab94985fdfba527ea25285a60be4',
        },
    }]

    def _acfun_user_video_page(self, user_id, pagesize, pagenum):
        page = pagenum + 1
        query = {
            'pageNo': page,
            'pageSize': pagesize,
            'userId': user_id,
            'type': 1,
        }
        info = self._acfun_api_v0(
            user_id, 'http://api.app.acfun.cn/apiserver/user/contribution',
            query=query,
            note='Downloading user videos info, page=%d' % page)
        for video in info['page']['list']:
            yield self._acfun_entry(video)

    def _acfun_user_info(self, user_id):
        info = self._acfun_api_v0(
            user_id, 'http://api.app.acfun.cn/apiserver/profile',
            query={'userId': user_id},
            note='Downloading user info')
        return info['fullUser']

    def _real_extract(self, url):
        user_id = self._match_id(url)
        user_info = self._acfun_user_info(user_id)
        paged = OnDemandPagedList(
            functools.partial(self._acfun_user_video_page, user_id, self._PAGE_SIZE),
            self._PAGE_SIZE, use_cache=True)
        return self._acfun_list({
            'title': user_info['username'],
            'description': user_info['signature'],
        }, user_id, paged)


class _AcFunAlbumIE(_AcFunListIE):
    _ACFUN_API_ALBUM = 'http://apipc.app.acfun.cn/albums/'
    _ACFUN_ALBUM_CACHE = {}

    def _acfun_album_group_page(self, album_id, group, pagesize, pagenum):
        contents = group['contents']
        if 0 == pagenum and len(contents) <= pagesize:
            return contents

        group_id = group['groupId']
        page = pagenum + 1
        query = {
            'groupId': group_id,
            'page': '{num:%d,size:%d}' % (page, pagesize),
        }
        info = self._acfun_api_v1(
            album_id, self._ACFUN_API_ALBUM + album_id[2:] + '/contents',
            query=query,
            note='Downloading Album group info, group=%d, page=%d' % (group_id, page))
        return info['list']

    def _acfun_album_info(self, album_id):
        if album_id in self._ACFUN_ALBUM_CACHE:
            return self._ACFUN_ALBUM_CACHE[album_id]
        album_info = self._acfun_api_v1(
            album_id, self._ACFUN_API_ALBUM + album_id[2:],
            note='Downloading Album info')
        album_groups = []
        for group in album_info.pop('groups'):
            paged = OnDemandPagedList(
                functools.partial(self._acfun_album_group_page, album_id, group, self._PAGE_SIZE),
                self._PAGE_SIZE)
            group['contents'] = paged.getslice()
            album_groups.append(group)
        album_info['groups'] = album_groups
        self._ACFUN_ALBUM_CACHE[album_id] = album_info
        return album_info


class AcFunAlbumGroupIE(_AcFunAlbumIE):
    IE_NAME = 'acfun:albumgroup'
    IE_DESC = False  # Do not list
    _VALID_URL = _ACFUN_HOST + r'/a/(?P<id>aa\d+)\#group=(?P<group>\d+)'
    _TESTS = [{
        'url': 'http://www.acfun.cn/a/aa5001561#group=1',
        'playlist_mincount': 5,
        'info_dict': {
            'id': 'ag2680',
            'title': '8分钟家庭锻炼_未分组',
            'description': '8分钟系列，适合无器械锻炼胸肌 腹肌',
        },
    }, {
        'url': 'http://www.acfun.cn/a/aa5016734#group=1',
        'playlist_mincount': 34,
        'info_dict': {
            'id': 'ag26859',
            'title': '番剧OPED_未分组',
            'description': 'md5:e0544b43a3f9c918218111cd32d9fdb7',
        },
    }]

    def _real_extract(self, url):
        album_id, group_idx = self._match_two(url, 'group')
        album_info = self._acfun_album_info(album_id)
        group_info = album_info['groups'][group_idx - 1]
        videos = [self._acfun_entry(v) for v in group_info['contents'] if not v['article']]
        return self._acfun_list({
            'title': '%s_%s' % (album_info['title'], group_info['groupName']),
            'description': self._get_desc(album_info),
        }, 'ag{}'.format(group_info['groupId']), videos)


class AcFunAlbumIE(_AcFunAlbumIE):
    IE_NAME = 'acfun:album'
    IE_DESC = 'AcFun - 合辑'
    _VALID_URL = _ACFUN_HOST + r'/a/(?P<id>aa\d+)$'
    _TESTS = [{
        'url': 'http://www.acfun.cn/a/aa5001107',
        'playlist_mincount': 4,
        'info_dict': {
            'id': 'aa5001107',
            'title': 'AcFun无聊大作战-视频',
            'description': 'md5:4962d13677feb34eda82f2f98202e1ee',
        },
    }, {
        'url': 'http://www.acfun.cn/a/aa5014197',
        'playlist_mincount': 19,
        'info_dict': {
            'id': 'aa5014197',
            'title': '第五届AcFun毁歌祭-视频',
            'description': 'md5:9d729d9127baaf8a0c66fd381a0a3d12',
        },
    }]

    def _real_extract(self, url):
        album_id = self._match_id(url)
        album_info = self._acfun_album_info(album_id)
        entries = [self.url_result(
            'http://www.acfun.cn/a/%s#group=%d' % (album_id, idx + 1),
            ie=AcFunAlbumGroupIE.ie_key(),
            video_title='%s_%s' % (album_info.get('title'), group['groupName']),
        ) for idx, group in enumerate(album_info['groups'])]
        return self.playlist_result(
            entries, album_id,
            album_info.get('title'), self._get_desc(album_info))
