# coding: utf-8
from __future__ import unicode_literals

import hashlib
import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    parse_iso8601,
    smuggle_url,
    strip_jsonp,
    unified_timestamp,
    unsmuggle_url,
    urlencode_postdata,
    unified_strdate,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|bangumi\.|)bilibili\.(?:tv|com)/'\
                 r'(?:video/av|anime/(?P<anime_id>\d+)/play#|bangumi/play/ep)(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '4f555e8de705b99b22215fcc774b0f9b',
        'info_dict': {
            'id': '1074402',
            'ext': 'mp4',
            'title': '【金坷垃】金泡沫',
            'description': 'md5:ce18c2a2d2193f0df2917d270f2e5923',
            'duration': 308.315,
            'timestamp': 1398012660,
            'upload_date': '20140420',
            'thumbnail': r're:^https?://.+\.jpg',
            'uploader': '菊子桑',
            'uploader_id': '156160',
        },
    }, {
        # Tested in BiliBiliBangumiIE
        'url': 'http://bangumi.bilibili.com/anime/1869/play#40062',
        'only_matching': True,
    }, {
        'url': 'http://bangumi.bilibili.com/anime/5802/play#100643',
        'md5': '3f721ad1e75030cc06faf73587cfec57',
        'info_dict': {
            'id': '100643',
            'ext': 'mp4',
            'title': 'CHAOS;CHILD',
            'description': '如果你是神明，并且能够让妄想成为现实。那你会进行怎么样的妄想？是淫靡的世界？独裁社会？毁灭性的制裁？'\
                           '还是……2015年，涩谷。从6年前发生的大灾害“涩谷地震”之后复兴了的这个街区里新设立的私立高中...',
        },
        'skip': 'Geo-restricted to China',
    }, {
        # Title with double quotes
        'url': 'http://www.bilibili.com/video/av8903802/',
        'info_dict': {
            'id': '8903802',
            'ext': 'mp4',
            'title': '阿滴英文｜英文歌分享#6 "Closer',
            'description': '滴妹今天唱Closer給你聽! 有史以来，被推最多次也是最久的歌曲，其实歌词跟我原本想像差蛮多的，不过还是好听！ 微博@阿滴英文',
            'uploader': '阿滴英文',
            'uploader_id': '65880958',
            'timestamp': 1488382620,
            'upload_date': '20170301',
        },
        'params': {
            'skip_download': True,  # Test metadata only
        },
    }, {
        # Another type of webpage
        'url': 'https://www.bilibili.com/video/av16492411/',
        'info_dict': {
            'id': '16492411',
            'ext': 'mp4',
            'title': '【游戏混剪】各种妹子',
            'description': 'md5:4729a611536a756821ab59ca217f0328',
            'duration': 187.65,
            'timestamp': 1511129700,
            'upload_date': '20171119',
            'thumbnail': r're:^https?://.+\.jpg',
            'uploader': '丁克Whovian',
            'uploader_id': '242283',
        },
    }, {
        'url': 'https://www.bilibili.com/bangumi/play/ep40062',
        'info_dict': {
            'id': '40062',
            'ext': 'mp4',
            'title': '混沌武士：第1话 疾风怒涛 Tempestuous Temperaments',
            'description': 'md5:f51e94a84b78f1cd6a9642807aad63b9',
            'duration': 1401.758,
            'timestamp': None,
            'upload_date': None,
            'thumbnail': r're:^https?://.+\.jpg',
            'uploader': '哔哩哔哩番剧',
            'uploader_id': None,
        },
    }, ]

    _APP_KEY = '84956560bc028eb7'
    _BILIBILI_KEY = '94aba54af9065f71de72f5508f1cd42e'

    def _report_error(self, result):
        if 'message' in result:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, result['message']), expected=True)
        elif 'code' in result:
            raise ExtractorError('%s returns error %d' % (self.IE_NAME, result['code']), expected=True)
        else:
            raise ExtractorError('Can\'t extract Bangumi episode ID')

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        anime_id = mobj.group('anime_id') or self._search_regex(
            r'["\']media_id["\']:(\d+)', webpage, 'anime_id', default=None)

        if ('bangumi/' in url) or ('anime/' in url):
            if 'no_bangumi_tip' not in smuggled_data:
                tip_url = compat_urlparse.urljoin(url, '//bangumi.bilibili.com/anime/%s' % anime_id)
                self.to_screen(
                    'Downloading episode %s. To download all videos in anime %s, re-run youtube-dl with %s' % (
                        video_id, anime_id, tip_url))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': url
            }
            headers.update(self.geo_verification_headers())

            js = self._download_json(
                'http://bangumi.bilibili.com/web_api/get_source', video_id,
                data=urlencode_postdata({'episode_id': video_id}),
                headers=headers)
            if 'result' not in js:
                self._report_error(js)
            cid = js['result']['cid']
        else:
            cid = self._search_regex(r'["\']cid["\']:(\d+)', webpage, 'cid', default=None) or\
                compat_parse_qs(
                    self._search_regex([r'EmbedPlayer\([^)]+,\s*"([^"]+)"\)',
                                        r'<iframe[^>]+src="https://secure\.bilibili\.com/secure,([^"]+)"'],
                                       webpage, 'player parameters'))['cid'][0]

        payload = 'appkey=%s&cid=%s&otype=json&quality=2&type=mp4' % (self._APP_KEY, cid)
        sign = hashlib.md5((payload + self._BILIBILI_KEY).encode('utf-8')).hexdigest()

        headers = {
            'Referer': url
        }
        headers.update(self.geo_verification_headers())

        video_info = self._download_json(
            'http://interface.bilibili.com/playurl?%s&sign=%s' % (payload, sign),
            video_id, note='Downloading video info page',
            headers=headers)

        if 'durl' not in video_info:
            self._report_error(video_info)

        entries = []

        for idx, durl in enumerate(video_info['durl']):
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
                'id': '%s_part%s' % (video_id, idx),
                'duration': float_or_none(durl.get('length'), 1000),
                'formats': formats,
            })

        if ('bangumi/' in url) or ('anime/' in url):
            description = self._html_search_meta('description', webpage, default=None)
        else:
            description = self._download_json(
                'https://api.bilibili.com/x/web-interface/archive/desc?aid=%s' %
                video_id, video_id, note='Downloading description', fatal=False, headers=headers).get('data') or\
                self._html_search_meta('description', webpage, default=None)

        title = self._html_search_regex(['<h1[^>]*>([^<]+)</h1>', r'<h1 title=["\']([^>]+)["\']>'], webpage, 'title')
        thumbnail = self._html_search_meta(['og:image', 'thumbnailUrl'], webpage, default=None)
        upload_date = self._html_search_meta('uploadDate', webpage, default=None)
        uploader = self._html_search_meta('author', webpage) or\
            self._search_regex(r'["\'](?:(?:upData)|(?:owner))["\']:.*["\']name["\']:["\']([^"\']+)["\']',
                               webpage, 'uploader', default=None)

        uploader_id = self._html_search_regex(
            r'["\'](?:(?:upData)|(?:owner))["\']:{["\']mid["\']:["\']?(\d+)(?:["\']|,)',
            webpage, 'uploader_id', default=None)

        timestamp = self._html_search_regex(r'<time[^>]+datetime="([^"]+)"', webpage, 'upload time', default=None)

        # For older webpage type
        uploader_mobj = re.search(
            r'<a[^>]+href="(?:https?:)?//space\.bilibili\.com/(?P<id>\d+)"[^>]+title="(?P<name>[^"]+)"',
            webpage)
        if uploader_mobj:
            uploader = uploader_mobj.group('name')
            uploader_id = uploader_mobj.group('id')

        # TODO 'view_count' requires deobfuscating Javascript
        info = {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': unified_timestamp(timestamp),
            'thumbnail': thumbnail,
            'duration': float_or_none(video_info.get('timelength'), scale=1000),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'upload_date': unified_strdate(upload_date),
        }

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


class BiliBiliBangumiIE(InfoExtractor):
    _VALID_URL = r'https?://bangumi\.bilibili\.com/anime/(?P<id>\d+)'

    IE_NAME = 'bangumi.bilibili.com'
    IE_DESC = 'BiliBili番剧'

    _TESTS = [{
        'url': 'http://bangumi.bilibili.com/anime/1869',
        'info_dict': {
            'id': '1869',
            'title': '混沌武士',
            'description': 'md5:6a9622b911565794c11f25f81d6a97d2',
        },
        'playlist_count': 26,
    }, {
        'url': 'http://bangumi.bilibili.com/anime/1869',
        'info_dict': {
            'id': '1869',
            'title': '混沌武士',
            'description': 'md5:6a9622b911565794c11f25f81d6a97d2',
        },
        'playlist': [{
            'md5': '94ae439d229fecd90888ce810204f0aa',
            'info_dict': {
                'id': '40062',
                'ext': 'mp4',
                'title': '混沌武士：第1话 疾风怒涛 Tempestuous Temperaments',
                'description': 'md5:f51e94a84b78f1cd6a9642807aad63b9',
                'timestamp': 1414538739,
                'upload_date': '20141028',
                'episode': '疾风怒涛 Tempestuous Temperaments',
                'episode_number': 1,
                'uploader': '哔哩哔哩番剧',
                'uploader_id': None,
            },
        }],
        'params': {
            'playlist_items': '1',
        },
    }]

    @classmethod
    def suitable(cls, url):
        return False if BiliBiliIE.suitable(url) else super(BiliBiliBangumiIE, cls).suitable(url)

    def _real_extract(self, url):
        bangumi_id = self._match_id(url)

        season_info = self._download_json(
            'http://bangumi.bilibili.com/jsonp/seasoninfo/%s.ver?callback=seasonListCallback&jsonp=jsonp' % bangumi_id,
            bangumi_id, transform_source=strip_jsonp)['result']

        entries = [{
            '_type': 'url_transparent',
            'url': smuggle_url(episode['webplay_url'], {'no_bangumi_tip': 1}),
            'ie_key': BiliBiliIE.ie_key(),
            'timestamp': parse_iso8601(episode.get('update_time'), delimiter=' '),
            'episode': episode.get('index_title'),
            'episode_number': int_or_none(episode.get('index')),
        } for episode in season_info['episodes']]

        entries = sorted(entries, key=lambda entry: entry.get('episode_number'))

        return self.playlist_result(
            entries, bangumi_id,
            season_info.get('bangumi_title'), season_info.get('evaluate'))
