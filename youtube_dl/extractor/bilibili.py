# coding: utf-8
from __future__ import unicode_literals

import hashlib
import re
import json

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
)


class BiliBiliIE(InfoExtractor): 
    _VALID_URL = r'https?://(?:www\.|bangumi\.|)bilibili\.(?:tv|com)/(?:video/av|anime/(?P<anime_id>\d+)/play#)(?P<id>\d+)'

    # url like:
    # + https://www.bilibili.com/video/av28152675
    # + https://www.bilibili.com/video/av28152675/?p=2
    _VALID_MULTI_P_URL = r'https?://(?:www\.|bangumi\.|)bilibili\.(?:tv|com)/video/av(?P<id>\d+)(/\?p=(?P<p_id>\d+))?'

    _TESTS = [{
        'url': 'https://www.bilibili.com/video/av28152675/?p=1',
        'md5': '3d0af4158af2e628eb2fc2cad2390da2',
        'info_dict': {
            'id': '28152675_p1',
            'ext': 'flv',
            'title': '【2020宏观系列-Ray Dalio】 桥水 达里奥的观点汇总__RAY DALIO- US economy looks like 1937 and we need to be careful',
            'description': 'YouTube2020宏观系列一代传奇桥水达里奥的观点汇总。1.美国经济就像1937年 US economy looks like 19372.有70%的概率2020前美国经济陷入衰退3.我们正处于一生一见的长债务周期末端持续补充',
            'duration': 222.791,
            'timestamp': 1533037003,
            'upload_date': '20180731',
            'thumbnail': r're:^https?://.+\.jpg',
            'uploader': 'RaymondWarrior',
            'uploader_id': '599478',
        },
    }, {
        'url': 'https://www.bilibili.com/video/av28152675/?p=2',
        'md5': '2ebe1cc8ed1ff74d6c0871b54369ec83',
        'info_dict': {
            'id': '28152675_p2',
            'ext': 'flv',
            'title': '【2020宏观系列-Ray Dalio】 桥水 达里奥的观点汇总__Ray Dalio- 70% Chance Of Recession By 2020',
            'description': 'YouTube2020宏观系列一代传奇桥水达里奥的观点汇总。1.美国经济就像1937年 US economy looks like 19372.有70%的概率2020前美国经济陷入衰退3.我们正处于一生一见的长债务周期末端持续补充',
            'duration': 237.481,
            'timestamp': 1533037003,
            'upload_date': '20180731',
            'thumbnail': r're:^https?://.+\.jpg',
            'uploader': 'RaymondWarrior',
            'uploader_id': '599478',
        },
    }, {
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '5f7d29e1a2872f3df0cf76b1f87d3788',
        'info_dict': {
            'id': '1074402',
            'ext': 'flv',
            'title': '【金坷垃】金泡沫',
            'description': 'md5:ce18c2a2d2193f0df2917d270f2e5923',
            'duration': 308.067,
            'timestamp': 1398012678,
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
            'description': '如果你是神明，并且能够让妄想成为现实。那你会进行怎么样的妄想？是淫靡的世界？独裁社会？毁灭性的制裁？还是……2015年，涩谷。从6年前发生的大灾害“涩谷地震”之后复兴了的这个街区里新设立的私立高中...',
        },
        'skip': 'Geo-restricted to China',
    }, {
        # Title with double quotes
        'url': 'http://www.bilibili.com/video/av8903802/',
        'info_dict': {
            'id': '8903802',
            'title': '阿滴英文｜英文歌分享#6 "Closer',
            'description': '滴妹今天唱Closer給你聽! 有史以来，被推最多次也是最久的歌曲，其实歌词跟我原本想像差蛮多的，不过还是好听！ 微博@阿滴英文',
        },
        'playlist': [{
            'info_dict': {
                'id': '8903802_part1',
                'ext': 'flv',
                'title': '阿滴英文｜英文歌分享#6 "Closer',
                'description': 'md5:3b1b9e25b78da4ef87e9b548b88ee76a',
                'uploader': '阿滴英文',
                'uploader_id': '65880958',
                'timestamp': 1488382634,
                'upload_date': '20170301',
            },
            'params': {
                'skip_download': True,  # Test metadata only
            },
        }, {
            'info_dict': {
                'id': '8903802_part2',
                'ext': 'flv',
                'title': '阿滴英文｜英文歌分享#6 "Closer',
                'description': 'md5:3b1b9e25b78da4ef87e9b548b88ee76a',
                'uploader': '阿滴英文',
                'uploader_id': '65880958',
                'timestamp': 1488382634,
                'upload_date': '20170301',
            },
            'params': {
                'skip_download': True,  # Test metadata only
            },
        }]
    }]

    _APP_KEY = '84956560bc028eb7'
    _BILIBILI_KEY = '94aba54af9065f71de72f5508f1cd42e'

    def _report_error(self, result):
        if 'message' in result:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, result['message']), expected=True)
        elif 'code' in result:
            raise ExtractorError('%s returns error %d' % (self.IE_NAME, result['code']), expected=True)
        else:
            raise ExtractorError('Can\'t extract Bangumi episode ID')

    def _extract_pages_info(self, pages_array_json_str, page_id):
        why_wrong_msg = "This may be caused by: 1. Your url is not correct.  " + \
                        "2. Bilibili has change the format (someone needs to update this tool for the change.)"

        try:
            pages_array = json.loads(pages_array_json_str)
        except Exception:
            raise ExtractorError(
                "Failed to parse \"pages\" info as JSON for your Bilibili url. " + why_wrong_msg
            )

        if not isinstance(pages_array, type([])):
            raise ExtractorError(
                "\"pages\" info JSON object is not an Array for your Bilibili url. " + why_wrong_msg
            )
        for page_obj in pages_array:
            if not isinstance(page_obj, type({})):
                raise ExtractorError(
                    "\"page\" object in \"pages\" JSON Array is not an Map for your Bilibili url. " + why_wrong_msg
                )
            if page_id == str(page_obj["page"]):
                return (page_obj["cid"], page_obj["part"])

        raise ExtractorError(
            "We can't find page {} in \"pages\" Object from your Bilibili url. ".format(page_id) + why_wrong_msg
        )

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        page_name = None
        if 'anime/' not in url:
            mobj = re.match(self._VALID_MULTI_P_URL, url)
            video_id = mobj.group('id')
            anime_id = None
            page_id = mobj.group('p_id')
            webpage = self._download_webpage(url, video_id)

            if page_id is None:
                cid = self._search_regex(
                    r'\bcid(?:["\']:|=)(\d+)', webpage, 'cid',
                    default=None
                ) or compat_parse_qs(self._search_regex(
                    [r'EmbedPlayer\([^)]+,\s*"([^"]+)"\)',
                     r'EmbedPlayer\([^)]+,\s*\\"([^"]+)\\"\)',
                     r'<iframe[^>]+src="https://secure\.bilibili\.com/secure,([^"]+)"'],
                    webpage, 'player parameters'))['cid'][0]
            else:
                pages_array_json_str = self._search_regex(
                    r'(?:"pages":)(\[[^\[\]]*\])', webpage, 'pages',
                    default=None
                )
                (cid, page_name) = self._extract_pages_info(pages_array_json_str, page_id)

        else:
            mobj = re.match(self._VALID_URL, url)
            video_id = mobj.group('id')
            anime_id = mobj.group('anime_id')
            webpage = self._download_webpage(url, video_id)

            if 'no_bangumi_tip' not in smuggled_data:
                self.to_screen('Downloading episode %s. To download all videos in anime %s, re-run youtube-dl with %s' % (
                    video_id, anime_id, compat_urlparse.urljoin(url, '//bangumi.bilibili.com/anime/%s' % anime_id)))
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

        headers = {
            'Referer': url
        }
        headers.update(self.geo_verification_headers())

        entries = []

        RENDITIONS = ('qn=80&quality=80&type=', 'quality=2&type=mp4')
        for num, rendition in enumerate(RENDITIONS, start=1):
            payload = 'appkey=%s&cid=%s&otype=json&%s' % (self._APP_KEY, cid, rendition)
            sign = hashlib.md5((payload + self._BILIBILI_KEY).encode('utf-8')).hexdigest()

            video_info = self._download_json(
                'http://interface.bilibili.com/v2/playurl?%s&sign=%s' % (payload, sign),
                video_id, note='Downloading video info page',
                headers=headers, fatal=num == len(RENDITIONS))

            if not video_info:
                continue

            if 'durl' not in video_info:
                if num < len(RENDITIONS):
                    continue
                self._report_error(video_info)

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
            break

        title = self._html_search_regex(
            ('<h1[^>]+\btitle=(["\'])(?P<title>(?:(?!\1).)+)\1',
             '(?s)<h1[^>]*>(?P<title>.+?)</h1>'), webpage, 'title',
            group='title')
        description = self._html_search_meta('description', webpage)
        timestamp = unified_timestamp(self._html_search_regex(
            r'<time[^>]+datetime="([^"]+)"', webpage, 'upload time',
            default=None) or self._html_search_meta(
            'uploadDate', webpage, 'timestamp', default=None))
        thumbnail = self._html_search_meta(['og:image', 'thumbnailUrl'], webpage)

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
            r'<a[^>]+href="(?:https?:)?//space\.bilibili\.com/(?P<id>\d+)"[^>]*>(?P<name>[^<]+)',
            webpage)
        if uploader_mobj:
            info.update({
                'uploader': uploader_mobj.group('name'),
                'uploader_id': uploader_mobj.group('id'),
            })
        if not info.get('uploader'):
            info['uploader'] = self._html_search_meta(
                'author', webpage, 'uploader', default=None)

        for entry in entries:
            entry.update(info)

        if len(entries) == 1:
            if page_name is not None:
                entries[0]['id'] += "_p{}".format(page_id)
                entries[0]['title'] += "__{}".format(page_name)
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
            'md5': '91da8621454dd58316851c27c68b0c13',
            'info_dict': {
                'id': '40062',
                'ext': 'mp4',
                'title': '混沌武士',
                'description': '故事发生在日本的江户时代。风是一个小酒馆的打工女。一日，酒馆里来了一群恶霸，虽然他们的举动令风十分不满，但是毕竟风只是一届女流，无法对他们采取什么行动，只能在心里嘟哝。这时，酒家里又进来了个“不良份子...',
                'timestamp': 1414538739,
                'upload_date': '20141028',
                'episode': '疾风怒涛 Tempestuous Temperaments',
                'episode_number': 1,
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

        # Sometimes this API returns a JSONP response
        season_info = self._download_json(
            'http://bangumi.bilibili.com/jsonp/seasoninfo/%s.ver' % bangumi_id,
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
