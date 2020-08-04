# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    smuggle_url,
    str_or_none,
    strip_jsonp,
    unsmuggle_url,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:(?:www)\.)?
                        bilibili\.(?:tv|com)/
                        (?:
                            (?:
                                video/[aA][vV]
                            )(?P<id_bv>\d+)|
                            video/[bB][vV](?P<id>[^/?#&]+)
                        )
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
            'timestamp': 1398012678,
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
    }, {
        # new BV video id format
        'url': 'https://www.bilibili.com/video/BV1JE411F741',
        'only_matching': True,
    }]

    _APP_KEY = 'iVGUTjsxvpLeuDCf'
    _BILIBILI_KEY = 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'

    def _report_error(self, result):
        if 'message' in result:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, result['message']), expected=True)
        elif 'code' in result:
            raise ExtractorError('%s returns error %d' % (self.IE_NAME, result['code']), expected=True)
        else:
            raise ExtractorError('Can\'t extract Bangumi episode ID')

    def _getfps(self, s):
        "convert fps to int"
        if s.isnumeric():
            return int(s)
        else:
            r = re.search(r"([0-9]+)/([0-9]+)", s)
            if r is not None:
                r = r.groups()
                return int(r[0]) / int(r[1])
            else:
                return 0

    def _calculate_size(self, durl):
        "Calculate total file size."
        s = 0
        for i in durl:
            s = s + i['size']
        return s

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('id_bv')
        query = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        part = None
        if 'p' in query and str(query['p'][0]).isnumeric():
            part = int(query['p'][0])

        # Set Cookies need to parse the Links.
        self._set_cookie(domain=".bilibili.com", name="CURRENT_QUALITY", value="120")  # Set default video quality
        self._set_cookie(domain=".bilibili.com", name="CURRENT_FNVAL", value="16")
        self._set_cookie(domain=".bilibili.com", name="laboratory", value="1-1")  # Use new webpage API
        self._set_cookie(domain=".bilibili.com", name="stardustvideo", value="1")

        webpage = self._download_webpage(url, video_id)

        video_info = re.search(r"window\.__INITIAL_STATE__=([^;]+)", webpage, re.I)
        if video_info is not None:
            video_info = json.loads(video_info.groups()[0])
        else:
            self._report_error("")  # TODO Should redirect to Bangumi episode ID.
            # https://api.bilibili.com/x/web-interface/view/detail?bvid=&aid=&jsonp=jsonp have redirect links.
        video_data = video_info['videoData']
        uploader_data = video_info['upData']
        aid = video_data['aid']
        bvid = video_data['bvid']
        video_count = video_data['videos']

        tags_info = self._download_json(
            f"https://api.bilibili.com/x/web-interface/view/detail/tag?aid={aid}", video_id,
            'Geting video tags.', 'Unable to get Login/User Information.')
        if tags_info['code'] != 0:
            self._report_error(tags_info)
        tags_info = tags_info['data']
        tags = []
        for i in tags_info:
            tags.append(i['tag_name'])

        user_info = self._download_json("https://api.bilibili.com/x/web-interface/nav", video_id,
                                        "Geting Login/User Information.", "Unable to get Login/User Information.")
        if user_info['code'] != 0 and user_info['code'] != -101:
            self._report_error(user_info)
        user_info = user_info['data']
        is_login = user_info['isLogin']
        if is_login:
            is_vip = user_info['vipStatus']
        else:
            is_vip = 0
        is_durl = False  # If return the durl Stream, this will be true

        info = {
            'id': video_id,
            'title': video_data['title'],
            'description': video_data['desc'],
            'timestamp': video_data['ctime'],
            'thumbnail': video_data['pic'],
            'uploader': uploader_data['name'],
            'uploader_id': uploader_data['mid'],
            'duration': video_data['duration'],
            'webpage_url': f'https://www.bilibili.com/video/av{aid}',
            'categories': [video_data['tname']],
            'view_count': video_data['stat']['viewseo'],
            'comment_count': video_data['stat']['reply'],
            'tags': tags
        }

        if video_count == 1:
            info.update({'alt_title': video_data['pages'][0]['part']})

        new_api = True  # Parse video links from webpage first.
        first = True  # First Part of List
        entries = []

        for part_info in video_data['pages']:
            if part is not None and part_info["page"] != part:
                continue
            uri = f'https://www.bilibili.com/video/av{aid}?p={part_info["page"]}'
            if first:
                first = False
            else:
                webpage = self._download_webpage(uri, f"{video_id} Part{part_info['page']}")
            headers = {'referer': uri}
            if new_api:
                play_info = re.search(r"window\.__playinfo__=([^<]+)", webpage, re.I)  # Get video links from webpage.
                if play_info is not None:
                    play_info = json.loads(play_info.groups()[0])
                    if play_info['code'] != 0:
                        self._report_error(play_info)
                    play_info = play_info['data']
                else:
                    new_api = False
                    play_info = self._download_json(
                        f"https://api.bilibili.com/x/player/playurl?cid={part_info['cid']}&qn=120&otype=json&bvid={bvid}&fnver=0&fnval=16",
                        f"{video_id} Part{part_info['page']}",
                        "Geting video links.",
                        "Unable to get video links.")
                    if play_info['code'] != 0:
                        self._report_error(play_info)
                    play_info = play_info['data']
            else:
                play_info = self._download_json(
                    f"https://api.bilibili.com/x/player/playurl?cid={part_info['cid']}&qn=120&otype=json&bvid={bvid}&fnver=0&fnval=16",
                    f"{video_id} Part{part_info['page']}",
                    "Geting video links.",
                    "Unable to get video links.")
                if play_info['code'] != 0:
                    self._report_error(play_info)
                play_info = play_info['data']
            if 'durl' in play_info:  # Stream for flv player
                if video_count > 1 and len(play_info['durl']) > 1 and part is None:
                    self.report_warning(
                        f"There are multiply FLV files in this part. Please input \"{uri}\" to extract it.",
                        f"{video_id} Part{part_info['page']}")
                    continue
                is_durl = True
                if video_count > 1:
                    info.update({
                        'title': f"{info['title']} - {part_info['part']}",
                        'id': f"{video_id} P{part_info['page']}"
                    })
                video_quality = play_info['quality']
                accept_video_quality_desc = play_info['accept_description']
                accept_video_quality = play_info['accept_quality']
                video_desc_dict = {}
                for i in range(len(accept_video_quality)):
                    video_desc_dict.update({
                        accept_video_quality[i]: accept_video_quality_desc[i]
                    })
                video_formats = {video_quality: play_info['durl']}
                video_formats_size = {video_quality: self._calculate_size(play_info['durl'])}  # Total Filesize Dict
                durl_length = [len(play_info['durl'])]
                for video_q in accept_video_quality:
                    if video_q not in video_formats:
                        if new_api:
                            self._set_cookie(domain=".bilibili.com", name="CURRENT_QUALITY", value=f"{video_q}")
                            webpage = self._download_webpage(uri,
                                                             f"{video_id} Part{part_info['page']}",
                                                             f"Geting video links for format id : {video_q}.",
                                                             f"Unable to get video links for format id : {video_q}.")
                            play_info = re.search(r"window\.__playinfo__=([^<]+)", webpage, re.I)  # Get video links from webpage.
                            if play_info is not None:
                                play_info = json.loads(play_info.groups()[0])
                                if play_info['code'] != 0:
                                    self._report_error(play_info)
                                play_info = play_info['data']
                            else:
                                new_api = False
                                play_info = self._download_json(
                                    f"https://api.bilibili.com/x/player/playurl?cid={part_info['cid']}&qn={video_q}&otype=json&bvid={bvid}&fnver=0&fnval=16", f"{video_id} Part{part_info['page']}",
                                    f"Geting video links for format id : {video_q}.",
                                    f"Unable to get video links for format id : {video_q}.")
                                if play_info['code'] != 0:
                                    self._report_error(play_info)
                                play_info = play_info['data']
                        else:
                            play_info = self._download_json(
                                f"https://api.bilibili.com/x/player/playurl?cid={part_info['cid']}&qn={video_q}&otype=json&bvid={bvid}&fnver=0&fnval=16", f"{video_id} Part{part_info['page']}",
                                f"Geting video links for format id : {video_q}.",
                                f"Unable to get video links for format id : {video_q}.")
                            if play_info['code'] != 0:
                                self._report_error(play_info)
                            play_info = play_info['data']
                        if 'durl' in play_info:
                            video_formats[play_info["quality"]] = play_info['durl']
                            video_formats_size[play_info["quality"]] = self._calculate_size(play_info['durl'])
                            durl_length.append(len(play_info['durl']))
                for i in range(max(durl_length)):
                    entry = {}
                    entry.update(info)
                    entry.update({'id': f"{info['id']} Part{i+1}"})
                    formats_output = []
                    for video_q in accept_video_quality:
                        durl = video_formats[video_q]
                        if i < len(durl):
                            video_format = durl[i]
                            formats_output.append({
                                "url": video_format['url'],
                                "format_id": f"{video_q}",
                                "ext": "flv",
                                "http_headers": headers,
                                "filesize": video_format['size']
                            })
                    entry['formats'] = formats_output
                    entries.append(entry)
            elif 'dash' in play_info:  # Stream for dash player
                video_quality = play_info['quality']
                accept_video_quality_desc = play_info['accept_description']
                accept_video_quality = play_info['accept_quality']
                accept_audio_quality = []
                dash = play_info['dash']
                video_quality_list = []
                video_desc_dict = {}
                for i in range(len(accept_video_quality)):
                    video_desc_dict.update({
                        accept_video_quality[i]: accept_video_quality_desc[i]
                    })
                video_formats = {}
                for video_format in dash['video']:
                    if video_format['codecs'].startswith('hev'):  # Let format id increase 1 to distinguish codec
                        video_quality_list.append(video_format['id'] + 1)
                        video_formats[video_format['id'] + 1] = video_format
                    else:
                        video_quality_list.append(video_format['id'])
                        video_formats[video_format['id']] = video_format
                bs = True  # Try to get all video formats
                while bs:
                    bs = False
                    for video_q in accept_video_quality:
                        if video_q not in video_formats:
                            if not is_login and video_q <= 32:
                                bs = True
                            elif is_vip < 1 and video_q <= 80 and video_q != 74:
                                bs = True
                            elif is_vip > 0:
                                bs = True
                            if new_api:
                                self._set_cookie(domain=".bilibili.com", name="CURRENT_QUALITY", value=f"{video_q}")
                                webpage = self._download_webpage(uri,
                                                                 f"{video_id} Part{part_info['page']}",
                                                                 f"Geting video links for format id : {video_q}.",
                                                                 f"Unable to get video links for format id : {video_q}.")
                                play_info = re.search(r"window\.__playinfo__=([^<]+)", webpage, re.I)  # Get video links from webpage.
                                if play_info is not None:
                                    play_info = json.loads(play_info.groups()[0])
                                    if play_info['code'] != 0:
                                        self._report_error(play_info)
                                    play_info = play_info['data']
                                else:
                                    new_api = False
                                    play_info = self._download_json(
                                        f"https://api.bilibili.com/x/player/playurl?cid={part_info['cid']}&qn={video_q}&otype=json&bvid={bvid}&fnver=0&fnval=16", f"{video_id} Part{part_info['page']}",
                                        f"Geting video links for format id : {video_q}.",
                                        f"Unable to get video links for format id : {video_q}.")
                                    if play_info['code'] != 0:
                                        self._report_error(play_info)
                                    play_info = play_info['data']
                            else:
                                play_info = self._download_json(
                                    f"https://api.bilibili.com/x/player/playurl?cid={part_info['cid']}&qn={video_q}&otype=json&bvid={bvid}&fnver=0&fnval=16",
                                    f"{video_id} Part{part_info['page']}",
                                    f"Geting video links for format id : {video_q}.",
                                    f"Unable to get video links for format id : {video_q}.")
                                if play_info['code'] != 0:
                                    self._report_error(play_info)
                                play_info = play_info['data']
                            if 'dash' in play_info:
                                for video_format in play_info['dash']['video']:
                                    if video_format['codecs'].startswith('hev'):  # Let format id increase 1 to distinguish codec
                                        video_format_q = video_format['id'] + 1
                                    else:
                                        video_format_q = video_format['id']
                                    if video_format_q not in video_formats:
                                        video_quality_list.append(video_format_q)
                                        video_formats[video_format_q] = video_format
                                        bs = True
                                break
                self._set_cookie(domain=".bilibili.com", name="CURRENT_QUALITY", value="120")
                entry = {}
                entry.update(info)
                formats_output = []
                for i in video_quality_list:
                    video_format = video_formats[i]
                    formats_output.append(
                        {"url": video_format['base_url'],
                         "ext": "mp4",
                         "format_note": video_desc_dict[video_format['id']],
                         "format_id": f"{i}",
                         "vcodec": video_format['codecs'],
                         "fps": self._getfps(video_format['frame_rate']),
                         "width": video_format['width'],
                         "height": video_format['height'],
                         "http_headers": headers
                         })
                if 'audio' in dash and dash['audio'] is not None:
                    for audio_format in dash['audio']:
                        accept_audio_quality.append(audio_format['id'])
                        video_formats[audio_format['id']] = audio_format
                accept_audio_quality.sort(reverse=True)
                for audio_quality in accept_audio_quality:
                    audio_format = video_formats[audio_quality]
                    formats_output.append({
                        "url": audio_format["base_url"],
                        "format_id": f"{audio_format['id']}",
                        "ext": "mp4",
                        "acodec": audio_format['codecs'],
                        "http_headers": headers
                    })
                entry.update({"formats": formats_output})
                if video_count > 1:
                    entry.update({"title": f"{info['title']} - {part_info['part']}"})
                    entry.update({"id": f"{video_id} P{part_info['page']}"})
                entries.append(entry)

        if video_count > 1:
            if len(entries) == 1 and not is_durl:
                info.update({
                    'formats': entries[0]['formats'],
                    'id': entries[0]['id']
                })
                return info
            info.update({
                "_type": 'multi_video',
                "entries": entries
            })
            return info
        else:
            if not is_durl:
                return entries[0]
            else:
                if len(entries) > 1:
                    info.update({
                        "_type": 'multi_video',
                        "entries": entries
                    })
                else:
                    info.update({
                        "formats": entries[0]['formats']
                    })
                return info


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
        'playlist_count': 19,
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
