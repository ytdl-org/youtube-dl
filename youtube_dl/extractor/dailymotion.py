# coding: utf-8
from __future__ import unicode_literals

import re
import json
import itertools

from .common import InfoExtractor
from .subtitles import SubtitlesInfoExtractor

from ..utils import (
    compat_urllib_request,
    compat_str,
    orderedSet,
    str_to_int,
    int_or_none,
    ExtractorError,
    unescapeHTML,
)


class DailymotionBaseInfoExtractor(InfoExtractor):
    @staticmethod
    def _build_request(url):
        """Build a request with the family filter disabled"""
        request = compat_urllib_request.Request(url)
        request.add_header('Cookie', 'family_filter=off')
        request.add_header('Cookie', 'ff=off')
        return request


class DailymotionIE(DailymotionBaseInfoExtractor, SubtitlesInfoExtractor):
    """Information Extractor for Dailymotion"""

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
            'url': 'http://www.dailymotion.com/video/x33vw9_tutoriel-de-youtubeur-dl-des-video_tech',
            'md5': '392c4b85a60a90dc4792da41ce3144eb',
            'info_dict': {
                'id': 'x33vw9',
                'ext': 'mp4',
                'uploader': 'Amphora Alex and Van .',
                'title': 'Tutoriel de Youtubeur"DL DES VIDEO DE YOUTUBE"',
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
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'http://www.dailymotion.com/video/%s' % video_id

        # Retrieve video webpage to extract further information
        request = self._build_request(url)
        webpage = self._download_webpage(request, video_id)

        # Extract URL, uploader and title from webpage
        self.report_extraction(video_id)

        # It may just embed a vevo video:
        m_vevo = re.search(
            r'<link rel="video_src" href="[^"]*?vevo.com[^"]*?video=(?P<id>[\w]*)',
            webpage)
        if m_vevo is not None:
            vevo_id = m_vevo.group('id')
            self.to_screen('Vevo video detected: %s' % vevo_id)
            return self.url_result('vevo:%s' % vevo_id, ie='Vevo')

        age_limit = self._rta_search(webpage)

        video_upload_date = None
        mobj = re.search(r'<div class="[^"]*uploaded_cont[^"]*" title="[^"]*">([0-9]{2})-([0-9]{2})-([0-9]{4})</div>', webpage)
        if mobj is not None:
            video_upload_date = mobj.group(3) + mobj.group(2) + mobj.group(1)

        embed_url = 'http://www.dailymotion.com/embed/video/%s' % video_id
        embed_page = self._download_webpage(embed_url, video_id,
                                            'Downloading embed page')
        info = self._search_regex(r'var info = ({.*?}),$', embed_page,
                                  'video info', flags=re.MULTILINE)
        info = json.loads(info)
        if info.get('error') is not None:
            msg = 'Couldn\'t get video, Dailymotion says: %s' % info['error']['title']
            raise ExtractorError(msg, expected=True)

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
        if not formats:
            raise ExtractorError('Unable to extract video URL')

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, webpage)
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, webpage)
            return

        view_count = str_to_int(self._search_regex(
            r'video_views_count[^>]+>\s+([\d\.,]+)',
            webpage, 'view count', fatal=False))

        title = self._og_search_title(webpage, default=None)
        if title is None:
            title = self._html_search_regex(
                r'(?s)<span\s+id="video_title"[^>]*>(.*?)</span>', webpage,
                'title')

        return {
            'id': video_id,
            'formats': formats,
            'uploader': info['owner.screenname'],
            'upload_date': video_upload_date,
            'title': title,
            'subtitles': video_subtitles,
            'thumbnail': info['thumbnail_url'],
            'age_limit': age_limit,
            'view_count': view_count,
        }

    def _get_available_subtitles(self, video_id, webpage):
        try:
            sub_list = self._download_webpage(
                'https://api.dailymotion.com/video/%s/subtitles?fields=id,language,url' % video_id,
                video_id, note=False)
        except ExtractorError as err:
            self._downloader.report_warning('unable to download video subtitles: %s' % compat_str(err))
            return {}
        info = json.loads(sub_list)
        if (info['total'] > 0):
            sub_lang_list = dict((l['language'], l['url']) for l in info['list'])
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
        },
        'playlist_mincount': 20,
    }]

    def _extract_entries(self, id):
        video_ids = []
        for pagenum in itertools.count(1):
            request = self._build_request(self._PAGE_TEMPLATE % (id, pagenum))
            webpage = self._download_webpage(request,
                                             id, 'Downloading page %s' % pagenum)

            video_ids.extend(re.findall(r'data-xid="(.+?)"', webpage))

            if re.search(self._MORE_PAGES_INDICATOR, webpage) is None:
                break
        return [self.url_result('http://www.dailymotion.com/video/%s' % video_id, 'Dailymotion')
                for video_id in orderedSet(video_ids)]

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
    _VALID_URL = r'https?://(?:www\.)?dailymotion\.[a-z]{2,3}/user/(?P<user>[^/]+)'
    _PAGE_TEMPLATE = 'http://www.dailymotion.com/user/%s/%s'
    _TESTS = [{
        'url': 'https://www.dailymotion.com/user/nqtv',
        'info_dict': {
            'id': 'nqtv',
            'title': 'Rémi Gaillard',
        },
        'playlist_mincount': 100,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user = mobj.group('user')
        webpage = self._download_webpage(url, user)
        full_user = unescapeHTML(self._html_search_regex(
            r'<a class="nav-image" title="([^"]+)" href="/%s">' % re.escape(user),
            webpage, 'user'))

        return {
            '_type': 'playlist',
            'id': user,
            'title': full_user,
            'entries': self._extract_entries(user),
        }
