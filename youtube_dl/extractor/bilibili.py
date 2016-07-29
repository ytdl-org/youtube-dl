# coding: utf-8
from __future__ import unicode_literals

import hashlib
import re

from .common import InfoExtractor
from ..compat import compat_parse_qs
from ..utils import (
    int_or_none,
    float_or_none,
    unified_timestamp,
)

HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'https?://(www.|bangumi.|)bilibili\.(?:tv|com)/(video/av|anime/v/)(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '9fa226fe2b8a9a4d5a69b4c6a183417e',
        'info_dict': {
            'id': '1074402',
            'ext': 'mp4',
            'title': '【金坷垃】金泡沫',
            'description': 'md5:ce18c2a2d2193f0df2917d270f2e5923',
            'duration': 308.315,
            'timestamp': 1398012660,
            'upload_date': '20140420',
            'thumbnail': 're:^https?://.+\.jpg',
            'uploader': '菊子桑',
            'uploader_id': '156160',
        },
    }, {
        'url': 'http://www.bilibili.com/video/av1041170/',
        'info_dict': {
            'id': '1041170',
            'ext': 'mp4',
            'title': '【BD1080P】刀语【诸神&异域】',
            'description': '这是个神奇的故事~每个人不留弹幕不给走哦~切利哦！~',
            'duration': 3382.259,
            'timestamp': 1396530060,
            'upload_date': '20140403',
            'thumbnail': 're:^https?://.+\.jpg',
            'uploader': '枫叶逝去',
            'uploader_id': '520116',
        },
    }, {
        'url': 'http://www.bilibili.com/video/av4808130/',
        'info_dict': {
            'id': '4808130',
            'ext': 'mp4',
            'title': '【长篇】哆啦A梦443【钉铛】',
            'description': '(2016.05.27)来组合客人的脸吧&amp;amp;寻母六千里锭 抱歉，又轮到周日上班现在才到家 封面www.pixiv.net/member_illust.php?mode=medium&amp;amp;illust_id=56912929',
            'duration': 1493.995,
            'timestamp': 1464564180,
            'upload_date': '20160529',
            'thumbnail': 're:^https?://.+\.jpg',
            'uploader': '喜欢拉面',
            'uploader_id': '151066',
        },
    }, {
        # Missing upload time
        'url': 'http://www.bilibili.com/video/av1867637/',
        'info_dict': {
            'id': '1867637',
            'ext': 'mp4',
            'title': '【HDTV】【喜剧】岳父岳母真难当 （2014）【法国票房冠军】',
            'description': '一个信奉天主教的法国旧式传统资产阶级家庭中有四个女儿。三个女儿却分别找了阿拉伯、犹太、中国丈夫，老夫老妻唯独期盼剩下未嫁的小女儿能找一个信奉天主教的法国白人，结果没想到小女儿找了一位非裔黑人……【这次应该不会跳帧了】',
            'duration': 5760.0,
            'uploader': '黑夜为猫',
            'uploader_id': '610729',
            'thumbnail': 're:^https?://.+\.jpg',
        },
        'params': {
            # Just to test metadata extraction
            'skip_download': True,
        },
        'expected_warnings': ['upload time'],
    }, {
        'url': 'http://bangumi.bilibili.com/anime/v/40068',
        'md5': '08d539a0884f3deb7b698fb13ba69696',
        'info_dict': {
            'id': '40068',
            'ext': 'mp4',
            'duration': 1402.357,
            'title': '混沌武士 : 第7集 四面楚歌 A Risky Racket',
            'description': "故事发生在日本的江户时代。风是一个小酒馆的打工女。一日，酒馆里来了一群恶霸，虽然他们的举动令风十分不满，但是毕竟风只是一届女流，无法对他们采取什么行动，只能在心里嘟哝。这时，酒家里又进来了个“不良份子”无幻，说以50个丸子帮她搞定这群人，风觉得他莫名其妙，也就没多搭理他。而在这时，风因为一个意外而将茶水泼在了恶霸头领——龙次郎身上。愤怒的恶霸们欲将风的手指砍掉，风在无奈中大喊道：“丸子100个！”…… 　　另一方面，龙次郎的父亲也就是当地的代官，依仗自己有着雄厚的保镖实力，在当地欺压穷人，当看到一穷人无法交齐足够的钱过桥时，欲下令将其杀死，武士仁看不惯这一幕，于是走上前，与代官的保镖交手了…… 　　酒馆内，因为风答应给无幻100个团子，无幻将恶霸们打败了，就在这时，仁进来了。好战的无幻立刻向仁发了战书，最后两败俱伤，被代官抓入牢房，预计第二天斩首…… 　　得知该状况的风，为报救命之恩，来到了刑场，利用烟花救出了无幻和仁。而风则以救命恩人的身份，命令二人和她一起去寻找带着向日葵香味的武士……(by百科)",
            'thumbnail': 're:^http?://.+\.jpg',
        },
    }]

    _APP_KEY = '6f90a59ac58a4123'
    _BILIBILI_KEY = '0bfd84cc3940035173f35e6777508326'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        _is_episode = 'anime/v' in url
        if not _is_episode:
            cid = compat_parse_qs(self._search_regex(
                [r'EmbedPlayer\([^)]+,\s*"([^"]+)"\)',
                r'<iframe[^>]+src="https://secure\.bilibili\.com/secure,([^"]+)"'],
                webpage, 'player parameters'))['cid'][0]
        else:
            url_t = 'http://bangumi.bilibili.com/web_api/get_source'
            js = self._download_json(url_t, video_id,
                                     data='episode_id=%s' % video_id,
                                     headers=HEADERS)
            cid = js['result']['cid']

        payload = 'appkey=%s&cid=%s&otype=json&quality=2&type=mp4' % (self._APP_KEY, cid)
        sign = hashlib.md5((payload + self._BILIBILI_KEY).encode('utf-8')).hexdigest()

        video_info = self._download_json(
            'http://interface.bilibili.com/playurl?%s&sign=%s' % (payload, sign),
            video_id, note='Downloading video info page')

        entries = []

        for idx, durl in enumerate(video_info['durl']):
            formats = [{
                'url': durl['url'],
                'filesize': int_or_none(durl['size']),
            }]
            for backup_url in durl['backup_url']:
                formats.append({
                    'url': backup_url,
                    # backup URLs have lower priorities
                    'preference': -2 if 'hd.mp4' in backup_url else -3,
                })

            self._sort_formats(formats)

            entries.append({
                'id': '%s_part%s' % (video_id, idx),
                'duration': float_or_none(durl.get('length'), 1000),
                'formats': formats,
            })

        title = self._html_search_regex('<h1[^>]+title="([^"]+)">', webpage, 'title')
        description = self._html_search_meta('description', webpage)
        timestamp = unified_timestamp(self._html_search_regex(
            r'<time[^>]+datetime="([^"]+)"', webpage, 'upload time', fatal=False))
        if _is_episode:
            thumbnail = self._html_search_meta('og:image', webpage)
        else:
            thumbnail = self._html_search_meta('thumbnailUrl', webpage)

        # TODO 'view_count' requires deobfuscating Javascript
        info = {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'thumbnail': thumbnail,
            'duration': float_or_none(video_info.get('timelength'), scale=1000),
        }

        uploader_mobj = re.search(
            r'<a[^>]+href="https?://space\.bilibili\.com/(?P<id>\d+)"[^>]+title="(?P<name>[^"]+)"',
            webpage)
        if uploader_mobj:
            info.update({
                'uploader': uploader_mobj.group('name'),
                'uploader_id': uploader_mobj.group('id'),
            })

        for entry in entries:
            entry.update(info)

        if len(entries) == 1:
            return entries[0]
        else:
            for idx, entry in enumerate(entries):
                entry['id'] = '%s_part%d' % (video_id, (idx + 1))

            return {
                '_type': 'multi_video',
                'id': video_id,
                'title': title,
                'description': description,
                'entries': entries,
            }
