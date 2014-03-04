import re
import json
import itertools

from .common import InfoExtractor
from .subtitles import SubtitlesInfoExtractor

from ..utils import (
    compat_urllib_request,
    compat_str,
    get_element_by_attribute,
    get_element_by_id,
    orderedSet,
    str_to_int,
    int_or_none,

    ExtractorError,
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
    IE_NAME = u'dailymotion'

    _FORMATS = [
        (u'stream_h264_ld_url', u'ld'),
        (u'stream_h264_url', u'standard'),
        (u'stream_h264_hq_url', u'hq'),
        (u'stream_h264_hd_url', u'hd'),
        (u'stream_h264_hd1080_url', u'hd180'),
    ]

    _TESTS = [
        {
            u'url': u'http://www.dailymotion.com/video/x33vw9_tutoriel-de-youtubeur-dl-des-video_tech',
            u'file': u'x33vw9.mp4',
            u'md5': u'392c4b85a60a90dc4792da41ce3144eb',
            u'info_dict': {
                u"uploader": u"Amphora Alex and Van .", 
                u"title": u"Tutoriel de Youtubeur\"DL DES VIDEO DE YOUTUBE\""
            }
        },
        # Vevo video
        {
            u'url': u'http://www.dailymotion.com/video/x149uew_katy-perry-roar-official_musi',
            u'file': u'USUV71301934.mp4',
            u'info_dict': {
                u'title': u'Roar (Official)',
                u'uploader': u'Katy Perry',
                u'upload_date': u'20130905',
            },
            u'params': {
                u'skip_download': True,
            },
            u'skip': u'VEVO is only available in some countries',
        },
        # age-restricted video
        {
            u'url': u'http://www.dailymotion.com/video/xyh2zz_leanna-decker-cyber-girl-of-the-year-desires-nude-playboy-plus_redband',
            u'file': u'xyh2zz.mp4',
            u'md5': u'0d667a7b9cebecc3c89ee93099c4159d',
            u'info_dict': {
                u'title': 'Leanna Decker - Cyber Girl Of The Year Desires Nude [Playboy Plus]',
                u'uploader': 'HotWaves1012',
                u'age_limit': 18,
            }

        }
    ]

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')

        url = 'http://www.dailymotion.com/video/%s' % video_id

        # Retrieve video webpage to extract further information
        request = self._build_request(url)
        webpage = self._download_webpage(request, video_id)

        # Extract URL, uploader and title from webpage
        self.report_extraction(video_id)

        # It may just embed a vevo video:
        m_vevo = re.search(
            r'<link rel="video_src" href="[^"]*?vevo.com[^"]*?videoId=(?P<id>[\w]*)',
            webpage)
        if m_vevo is not None:
            vevo_id = m_vevo.group('id')
            self.to_screen(u'Vevo video detected: %s' % vevo_id)
            return self.url_result(u'vevo:%s' % vevo_id, ie='Vevo')

        age_limit = self._rta_search(webpage)

        video_upload_date = None
        mobj = re.search(r'<div class="[^"]*uploaded_cont[^"]*" title="[^"]*">([0-9]{2})-([0-9]{2})-([0-9]{4})</div>', webpage)
        if mobj is not None:
            video_upload_date = mobj.group(3) + mobj.group(2) + mobj.group(1)

        embed_url = 'http://www.dailymotion.com/embed/video/%s' % video_id
        embed_page = self._download_webpage(embed_url, video_id,
                                            u'Downloading embed page')
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
            raise ExtractorError(u'Unable to extract video URL')

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, webpage)
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, webpage)
            return

        view_count = self._search_regex(
            r'video_views_count[^>]+>\s+([\d\.,]+)', webpage, u'view count', fatal=False)
        if view_count is not None:
            view_count = str_to_int(view_count)

        return {
            'id':       video_id,
            'formats': formats,
            'uploader': info['owner_screenname'],
            'upload_date':  video_upload_date,
            'title':    self._og_search_title(webpage),
            'subtitles':    video_subtitles,
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
            self._downloader.report_warning(u'unable to download video subtitles: %s' % compat_str(err))
            return {}
        info = json.loads(sub_list)
        if (info['total'] > 0):
            sub_lang_list = dict((l['language'], l['url']) for l in info['list'])
            return sub_lang_list
        self._downloader.report_warning(u'video doesn\'t have subtitles')
        return {}


class DailymotionPlaylistIE(DailymotionBaseInfoExtractor):
    IE_NAME = u'dailymotion:playlist'
    _VALID_URL = r'(?:https?://)?(?:www\.)?dailymotion\.[a-z]{2,3}/playlist/(?P<id>.+?)/'
    _MORE_PAGES_INDICATOR = r'<div class="next">.*?<a.*?href="/playlist/.+?".*?>.*?</a>.*?</div>'
    _PAGE_TEMPLATE = 'https://www.dailymotion.com/playlist/%s/%s'

    def _extract_entries(self, id):
        video_ids = []
        for pagenum in itertools.count(1):
            request = self._build_request(self._PAGE_TEMPLATE % (id, pagenum))
            webpage = self._download_webpage(request,
                                             id, u'Downloading page %s' % pagenum)

            playlist_el = get_element_by_attribute(u'class', u'row video_list', webpage)
            video_ids.extend(re.findall(r'data-id="(.+?)"', playlist_el))

            if re.search(self._MORE_PAGES_INDICATOR, webpage, re.DOTALL) is None:
                break
        return [self.url_result('http://www.dailymotion.com/video/%s' % video_id, 'Dailymotion')
                   for video_id in orderedSet(video_ids)]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        webpage = self._download_webpage(url, playlist_id)

        return {'_type': 'playlist',
                'id': playlist_id,
                'title': get_element_by_id(u'playlist_name', webpage),
                'entries': self._extract_entries(playlist_id),
                }


class DailymotionUserIE(DailymotionPlaylistIE):
    IE_NAME = u'dailymotion:user'
    _VALID_URL = r'(?:https?://)?(?:www\.)?dailymotion\.[a-z]{2,3}/user/(?P<user>[^/]+)'
    _MORE_PAGES_INDICATOR = r'<div class="next">.*?<a.*?href="/user/.+?".*?>.*?</a>.*?</div>'
    _PAGE_TEMPLATE = 'http://www.dailymotion.com/user/%s/%s'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user = mobj.group('user')
        webpage = self._download_webpage(url, user)
        full_user = self._html_search_regex(
            r'<a class="label" href="/%s".*?>(.*?)</' % re.escape(user),
            webpage, u'user', flags=re.DOTALL)

        return {
            '_type': 'playlist',
            'id': user,
            'title': full_user,
            'entries': self._extract_entries(user),
        }
