# coding: utf-8
from __future__ import unicode_literals

import calendar
import datetime
import re

from .common import InfoExtractor
from ..compat import (
    compat_etree_fromstring,
    compat_str,
    compat_parse_qs,
    compat_xml_parse_error,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    xpath_text,
)


class BiliBiliIE(InfoExtractor):
    _WORKING = False

    _VALID_URL = r'https?://www\.bilibili\.(?:tv|com)/video/av(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '9fa226fe2b8a9a4d5a69b4c6a183417e',
        'info_dict': {
            'id': '1554319',
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
            'id': '1507019',
            'ext': 'mp4',
            'title': '【BD1080P】刀语【诸神&异域】',
            'description': '这是个神奇的故事~每个人不留弹幕不给走哦~切利哦！~',
            'timestamp': 1396530060,
            'upload_date': '20140403',
            'uploader': '枫叶逝去',
            'uploader_id': '520116',
        },
    }, {
        'url': 'http://www.bilibili.com/video/av4808130/',
        'info_dict': {
            'id': '7802182',
            'ext': 'mp4',
            'title': '【长篇】哆啦A梦443【钉铛】',
            'description': '(2016.05.27)来组合客人的脸吧&amp;amp;寻母六千里锭 抱歉，又轮到周日上班现在才到家 封面www.pixiv.net/member_illust.php?mode=medium&amp;amp;illust_id=56912929',
            'timestamp': 1464564180,
            'upload_date': '20160529',
            'uploader': '喜欢拉面',
            'uploader_id': '151066',
        },
    }, {
        # Missing upload time
        'url': 'http://www.bilibili.com/video/av1867637/',
        'info_dict': {
            'id': '2880301',
            'ext': 'mp4',
            'title': '【HDTV】【喜剧】岳父岳母真难当 （2014）【法国票房冠军】',
            'description': '一个信奉天主教的法国旧式传统资产阶级家庭中有四个女儿。三个女儿却分别找了阿拉伯、犹太、中国丈夫，老夫老妻唯独期盼剩下未嫁的小女儿能找一个信奉天主教的法国白人，结果没想到小女儿找了一位非裔黑人……【这次应该不会跳帧了】',
            'uploader': '黑夜为猫',
            'uploader_id': '610729',
        },
        'params': {
            # Just to test metadata extraction
            'skip_download': True,
        },
        'expected_warnings': ['upload time'],
    }]

    # BiliBili blocks keys from time to time. The current key is extracted from
    # the Android client
    # TODO: find the sign algorithm used in the flash player
    _APP_KEY = '86385cdc024c0f6c'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        params = compat_parse_qs(self._search_regex(
            [r'EmbedPlayer\([^)]+,\s*"([^"]+)"\)',
             r'<iframe[^>]+src="https://secure\.bilibili\.com/secure,([^"]+)"'],
            webpage, 'player parameters'))
        cid = params['cid'][0]

        info_xml_str = self._download_webpage(
            'http://interface.bilibili.com/v_cdn_play',
            cid, query={'appkey': self._APP_KEY, 'cid': cid},
            note='Downloading video info page')

        err_msg = None
        durls = None
        info_xml = None
        try:
            info_xml = compat_etree_fromstring(info_xml_str.encode('utf-8'))
        except compat_xml_parse_error:
            info_json = self._parse_json(info_xml_str, video_id, fatal=False)
            err_msg = (info_json or {}).get('error_text')
        else:
            err_msg = xpath_text(info_xml, './message')

        if info_xml is not None:
            durls = info_xml.findall('./durl')
        if not durls:
            if err_msg:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, err_msg), expected=True)
            else:
                raise ExtractorError('No videos found!')

        entries = []

        for durl in durls:
            size = xpath_text(durl, ['./filesize', './size'])
            formats = [{
                'url': durl.find('./url').text,
                'filesize': int_or_none(size),
            }]
            for backup_url in durl.findall('./backup_url/url'):
                formats.append({
                    'url': backup_url.text,
                    # backup URLs have lower priorities
                    'preference': -2 if 'hd.mp4' in backup_url.text else -3,
                })

            self._sort_formats(formats)

            entries.append({
                'id': '%s_part%s' % (cid, xpath_text(durl, './order')),
                'duration': int_or_none(xpath_text(durl, './length'), 1000),
                'formats': formats,
            })

        title = self._html_search_regex('<h1[^>]+title="([^"]+)">', webpage, 'title')
        description = self._html_search_meta('description', webpage)
        datetime_str = self._html_search_regex(
            r'<time[^>]+datetime="([^"]+)"', webpage, 'upload time', fatal=False)
        timestamp = None
        if datetime_str:
            timestamp = calendar.timegm(datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M').timetuple())

        # TODO 'view_count' requires deobfuscating Javascript
        info = {
            'id': compat_str(cid),
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'thumbnail': self._html_search_meta('thumbnailUrl', webpage),
            'duration': float_or_none(xpath_text(info_xml, './timelength'), scale=1000),
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
