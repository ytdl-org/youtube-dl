# coding: utf-8
from __future__ import unicode_literals

import re
import json
import itertools

from .common import InfoExtractor

from ..compat import compat_str
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_iso8601,
    sanitized_Request,
    str_to_int,
    unescapeHTML,
)


class DailymotionBaseInfoExtractor(InfoExtractor):
    @staticmethod
    def _build_request(url):
        """Build a request with the family filter disabled"""
        request = sanitized_Request(url)
        request.add_header('Cookie', 'family_filter=off; ff=off')
        return request

    def _download_webpage_handle_no_ff(self, url, *args, **kwargs):
        request = self._build_request(url)
        return self._download_webpage_handle(request, *args, **kwargs)

    def _download_webpage_no_ff(self, url, *args, **kwargs):
        request = self._build_request(url)
        return self._download_webpage(request, *args, **kwargs)


class DailymotionIE(DailymotionBaseInfoExtractor):
    _VALID_URL = r'(?i)(?:https?://)?(?:(www|touch)\.)?dailymotion\.[a-z]{2,3}/(?:(embed|#)/)?video/(?P<id>[^/?_]+)'
    IE_NAME = 'dailymotion'

    _FORMATS = [
        ('stream_h264_ld_url', 'ld'),
        ('stream_h264_url', 'standard'),
        ('stream_h264_hq_url', 'hq'),
        ('stream_h264_hd_url', 'hd'),
        ('stream_h264_hd1080_url', 'hd180'),
    ]

    _TESTS = [
        {
            'url': 'https://www.dailymotion.com/video/x2iuewm_steam-machine-models-pricing-listed-on-steam-store-ign-news_videogames',
            'md5': '2137c41a8e78554bb09225b8eb322406',
            'info_dict': {
                'id': 'x2iuewm',
                'ext': 'mp4',
                'title': 'Steam Machine Models, Pricing Listed on Steam Store - IGN News',
                'description': 'Several come bundled with the Steam Controller.',
                'thumbnail': 're:^https?:.*\.(?:jpg|png)$',
                'duration': 74,
                'timestamp': 1425657362,
                'upload_date': '20150306',
                'uploader': 'IGN',
                'uploader_id': 'xijv66',
                'age_limit': 0,
                'view_count': int,
                'comment_count': int,
            }
        },
        # Vevo video
        {
            'url': 'http://www.dailymotion.com/video/x149uew_katy-perry-roar-official_musi',
            'info_dict': {
                'title': 'Roar (Official)',
                'id': 'USUV71301934',
                'ext': 'mp4',
                'uploader': 'Katy Perry',
                'upload_date': '20130905',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'VEVO is only available in some countries',
        },
        # age-restricted video
        {
            'url': 'http://www.dailymotion.com/video/xyh2zz_leanna-decker-cyber-girl-of-the-year-desires-nude-playboy-plus_redband',
            'md5': '0d667a7b9cebecc3c89ee93099c4159d',
            'info_dict': {
                'id': 'xyh2zz',
                'ext': 'mp4',
                'title': 'Leanna Decker - Cyber Girl Of The Year Desires Nude [Playboy Plus]',
                'uploader': 'HotWaves1012',
                'age_limit': 18,
            }
        },
        # geo-restricted, player v5
        {
            'url': 'http://www.dailymotion.com/video/xhza0o',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage_no_ff(
            'https://www.dailymotion.com/video/%s' % video_id, video_id)

        age_limit = self._rta_search(webpage)

        description = self._og_search_description(webpage) or self._html_search_meta(
            'description', webpage, 'description')

        view_count = str_to_int(self._search_regex(
            [r'<meta[^>]+itemprop="interactionCount"[^>]+content="UserPlays:(\d+)"',
             r'video_views_count[^>]+>\s+([\d\.,]+)'],
            webpage, 'view count', fatal=False))
        comment_count = int_or_none(self._search_regex(
            r'<meta[^>]+itemprop="interactionCount"[^>]+content="UserComments:(\d+)"',
            webpage, 'comment count', fatal=False))

        player_v5 = self._search_regex(
            [r'buildPlayer\(({.+?})\);', r'playerV5\s*=\s*dmp\.create\([^,]+?,\s*({.+?})\);'],
            webpage, 'player v5', default=None)
        if player_v5:
            player = self._parse_json(player_v5, video_id)
            metadata = player['metadata']

            self._check_error(metadata)

            formats = []
            for quality, media_list in metadata['qualities'].items():
                for media in media_list:
                    media_url = media.get('url')
                    if not media_url:
                        continue
                    type_ = media.get('type')
                    if type_ == 'application/vnd.lumberjack.manifest':
                        continue
                    ext = determine_ext(media_url)
                    if type_ == 'application/x-mpegURL' or ext == 'm3u8':
                        m3u8_formats = self._extract_m3u8_formats(
                            media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                        if m3u8_formats:
                            formats.extend(m3u8_formats)
                    elif type_ == 'application/f4m' or ext == 'f4m':
                        f4m_formats = self._extract_f4m_formats(
                            media_url, video_id, preference=-1, f4m_id='hds', fatal=False)
                        if f4m_formats:
                            formats.extend(f4m_formats)
                    else:
                        f = {
                            'url': media_url,
                            'format_id': quality,
                        }
                        m = re.search(r'H264-(?P<width>\d+)x(?P<height>\d+)', media_url)
                        if m:
                            f.update({
                                'width': int(m.group('width')),
                                'height': int(m.group('height')),
                            })
                        formats.append(f)
            self._sort_formats(formats)

            title = metadata['title']
            duration = int_or_none(metadata.get('duration'))
            timestamp = int_or_none(metadata.get('created_time'))
            thumbnail = metadata.get('poster_url')
            uploader = metadata.get('owner', {}).get('screenname')
            uploader_id = metadata.get('owner', {}).get('id')

            subtitles = {}
            for subtitle_lang, subtitle in metadata.get('subtitles', {}).get('data', {}).items():
                subtitles[subtitle_lang] = [{
                    'ext': determine_ext(subtitle_url),
                    'url': subtitle_url,
                } for subtitle_url in subtitle.get('urls', [])]

            return {
                'id': video_id,
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
                'duration': duration,
                'timestamp': timestamp,
                'uploader': uploader,
                'uploader_id': uploader_id,
                'age_limit': age_limit,
                'view_count': view_count,
                'comment_count': comment_count,
                'formats': formats,
                'subtitles': subtitles,
            }

        # vevo embed
        vevo_id = self._search_regex(
            r'<link rel="video_src" href="[^"]*?vevo.com[^"]*?video=(?P<id>[\w]*)',
            webpage, 'vevo embed', default=None)
        if vevo_id:
            return self.url_result('vevo:%s' % vevo_id, 'Vevo')

        # fallback old player
        embed_page = self._download_webpage_no_ff(
            'https://www.dailymotion.com/embed/video/%s' % video_id,
            video_id, 'Downloading embed page')

        timestamp = parse_iso8601(self._html_search_meta(
            'video:release_date', webpage, 'upload date'))

        info = self._parse_json(
            self._search_regex(
                r'var info = ({.*?}),$', embed_page,
                'video info', flags=re.MULTILINE),
            video_id)

        self._check_error(info)

        formats = []
        for (key, format_id) in self._FORMATS:
            video_url = info.get(key)
            if video_url is not None:
                m_size = re.search(r'H264-(\d+)x(\d+)', video_url)
                if m_size is not None:
                    width, height = map(int_or_none, (m_size.group(1), m_size.group(2)))
                else:
                    width, height = None, None
                formats.append({
                    'url': video_url,
                    'ext': 'mp4',
                    'format_id': format_id,
                    'width': width,
                    'height': height,
                })
        self._sort_formats(formats)

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, webpage)

        title = self._og_search_title(webpage, default=None)
        if title is None:
            title = self._html_search_regex(
                r'(?s)<span\s+id="video_title"[^>]*>(.*?)</span>', webpage,
                'title')

        return {
            'id': video_id,
            'formats': formats,
            'uploader': info['owner.screenname'],
            'timestamp': timestamp,
            'title': title,
            'description': description,
            'subtitles': video_subtitles,
            'thumbnail': info['thumbnail_url'],
            'age_limit': age_limit,
            'view_count': view_count,
            'duration': info['duration']
        }

    def _check_error(self, info):
        if info.get('error') is not None:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, info['error']['title']), expected=True)

    def _get_subtitles(self, video_id, webpage):
        try:
            sub_list = self._download_webpage(
                'https://api.dailymotion.com/video/%s/subtitles?fields=id,language,url' % video_id,
                video_id, note=False)
        except ExtractorError as err:
            self._downloader.report_warning('unable to download video subtitles: %s' % compat_str(err))
            return {}
        info = json.loads(sub_list)
        if (info['total'] > 0):
            sub_lang_list = dict((l['language'], [{'url': l['url'], 'ext': 'srt'}]) for l in info['list'])
            return sub_lang_list
        self._downloader.report_warning('video doesn\'t have subtitles')
        return {}


class DailymotionPlaylistIE(DailymotionBaseInfoExtractor):
    IE_NAME = 'dailymotion:playlist'
    _VALID_URL = r'(?:https?://)?(?:www\.)?dailymotion\.[a-z]{2,3}/playlist/(?P<id>.+?)/'
    _MORE_PAGES_INDICATOR = r'(?s)<div class="pages[^"]*">.*?<a\s+class="[^"]*?icon-arrow_right[^"]*?"'
    _PAGE_TEMPLATE = 'https://www.dailymotion.com/playlist/%s/%s'
    _TESTS = [{
        'url': 'http://www.dailymotion.com/playlist/xv4bw_nqtv_sport/1#video=xl8v3q',
        'info_dict': {
            'title': 'SPORT',
            'id': 'xv4bw_nqtv_sport',
        },
        'playlist_mincount': 20,
    }]

    def _extract_entries(self, id):
        video_ids = set()
        processed_urls = set()
        for pagenum in itertools.count(1):
            page_url = self._PAGE_TEMPLATE % (id, pagenum)
            webpage, urlh = self._download_webpage_handle_no_ff(
                page_url, id, 'Downloading page %s' % pagenum)
            if urlh.geturl() in processed_urls:
                self.report_warning('Stopped at duplicated page %s, which is the same as %s' % (
                    page_url, urlh.geturl()), id)
                break

            processed_urls.add(urlh.geturl())

            for video_id in re.findall(r'data-xid="(.+?)"', webpage):
                if video_id not in video_ids:
                    yield self.url_result('http://www.dailymotion.com/video/%s' % video_id, 'Dailymotion')
                    video_ids.add(video_id)

            if re.search(self._MORE_PAGES_INDICATOR, webpage) is None:
                break

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        webpage = self._download_webpage(url, playlist_id)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': self._og_search_title(webpage),
            'entries': self._extract_entries(playlist_id),
        }


class DailymotionUserIE(DailymotionPlaylistIE):
    IE_NAME = 'dailymotion:user'
    _VALID_URL = r'https?://(?:www\.)?dailymotion\.[a-z]{2,3}/(?!(?:embed|#|video|playlist)/)(?:(?:old/)?user/)?(?P<user>[^/]+)'
    _PAGE_TEMPLATE = 'http://www.dailymotion.com/user/%s/%s'
    _TESTS = [{
        'url': 'https://www.dailymotion.com/user/nqtv',
        'info_dict': {
            'id': 'nqtv',
            'title': 'Rémi Gaillard',
        },
        'playlist_mincount': 100,
    }, {
        'url': 'http://www.dailymotion.com/user/UnderProject',
        'info_dict': {
            'id': 'UnderProject',
            'title': 'UnderProject',
        },
        'playlist_mincount': 1800,
        'expected_warnings': [
            'Stopped at duplicated page',
        ],
        'skip': 'Takes too long time',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user = mobj.group('user')
        webpage = self._download_webpage(
            'https://www.dailymotion.com/user/%s' % user, user)
        full_user = unescapeHTML(self._html_search_regex(
            r'<a class="nav-image" title="([^"]+)" href="/%s">' % re.escape(user),
            webpage, 'user'))

        return {
            '_type': 'playlist',
            'id': user,
            'title': full_user,
            'entries': self._extract_entries(user),
        }


class DailymotionCloudIE(DailymotionBaseInfoExtractor):
    _VALID_URL_PREFIX = r'http://api\.dmcloud\.net/(?:player/)?embed/'
    _VALID_URL = r'%s[^/]+/(?P<id>[^/?]+)' % _VALID_URL_PREFIX
    _VALID_EMBED_URL = r'%s[^/]+/[^\'"]+' % _VALID_URL_PREFIX

    _TESTS = [{
        # From http://www.francetvinfo.fr/economie/entreprises/les-entreprises-familiales-le-secret-de-la-reussite_933271.html
        # Tested at FranceTvInfo_2
        'url': 'http://api.dmcloud.net/embed/4e7343f894a6f677b10006b4/556e03339473995ee145930c?auth=1464865870-0-jyhsm84b-ead4c701fb750cf9367bf4447167a3db&autoplay=1',
        'only_matching': True,
    }, {
        # http://www.francetvinfo.fr/societe/larguez-les-amarres-le-cobaturage-se-developpe_980101.html
        'url': 'http://api.dmcloud.net/player/embed/4e7343f894a6f677b10006b4/559545469473996d31429f06?auth=1467430263-0-90tglw2l-a3a4b64ed41efe48d7fccad85b8b8fda&autoplay=1',
        'only_matching': True,
    }]

    @classmethod
    def _extract_dmcloud_url(self, webpage):
        mobj = re.search(r'<iframe[^>]+src=[\'"](%s)[\'"]' % self._VALID_EMBED_URL, webpage)
        if mobj:
            return mobj.group(1)

        mobj = re.search(
            r'<input[^>]+id=[\'"]dmcloudUrlEmissionSelect[\'"][^>]+value=[\'"](%s)[\'"]' % self._VALID_EMBED_URL,
            webpage)
        if mobj:
            return mobj.group(1)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage_no_ff(url, video_id)

        title = self._html_search_regex(r'<title>([^>]+)</title>', webpage, 'title')

        video_info = self._parse_json(self._search_regex(
            r'var\s+info\s*=\s*([^;]+);', webpage, 'video info'), video_id)

        # TODO: parse ios_url, which is in fact a manifest
        video_url = video_info['mp4_url']

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': video_info.get('thumbnail_url'),
        }
