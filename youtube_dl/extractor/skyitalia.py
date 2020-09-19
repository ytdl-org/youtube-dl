# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class SkyItaliaBaseIE(InfoExtractor):
    _GET_VIDEO_DATA = 'https://apid.sky.it/vdp/v1/getVideoData?token={token}&caller=sky&rendition=web&id={id}'
    _TOKEN = 'F96WlOd8yoFmLQgiqv6fNQRvHZcsWk5jDaYnDvhbiJk'
    _RES = {
        'low': [426, 240],
        'med': [640, 360],
        'high': [854, 480],
        'hd': [1280, 720]
    }

    def _extract_video_id(self, url):
        webpage = self._download_webpage(url, 'skyitalia')
        video_id = self._html_search_regex(
            [r'data-videoid=\"(\d+)\"',
             r'http://player\.sky\.it/social\?id=(\d+)\&'],
            webpage, 'video_id')
        if video_id:
            return video_id
        raise ExtractorError('Video not found')

    def _get_formats(self, video_id, token=_TOKEN):
        data_url = self._GET_VIDEO_DATA.replace('{id}', video_id)
        data_url = data_url.replace('{token}', token)
        video_data = self._parse_json(
            self._download_webpage(data_url, video_id),
            video_id
        )

        formats = []
        for q, r in self._RES.items():
            key = 'web_' + q + '_url'
            if key not in video_data:
                continue
            formats.append({
                'url': video_data[key],
                'format_id': q,
                'width': r[0],
                'height': r[1]
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data['title'],
            'thumbnail': video_data['thumb'],
            'formats': formats
        }


class SkyVideoItIE(SkyItaliaBaseIE):
    IE_NAME = 'video.sky.it'
    _VALID_URL = r'https?://video\.sky\.it/[0-9a-z-/]+-(?P<id>[0-9]{6})(?:$|\?)'

    _TESTS = [
        {
            'url': 'https://video.sky.it/sport/motogp/video/motogp-gp-emilia-romagna-highlights-prove-libere-616162',
            'md5': '9c03b590b06e5952d8051f0e02b0feca',
            'info_dict': {
                'id': '616162',
                'ext': 'mp4',
                'title': 'MotoGP, GP Emilia Romagna: gli highlights delle prove libere',
                'thumbnail': 'https://videoplatform.sky.it/thumbnail/2020/09/18/1600441214452_hl-libere-motogp-misano2_5602634_thumbnail_1.jpg',
            }
        },
        {
            'url': 'https://video.sky.it/sport/motogp/video/motogp-gp-emilia-romagna-highlights-prove-libere-616162?itm_source=parsely-api',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        return self._get_formats(self._match_id(url))


class SkySportItIE(SkyItaliaBaseIE):
    IE_NAME = 'sport.sky.it'
    _VALID_URL = r'https?://sport\.sky\.it/.+?$'

    _TESTS = [
        {
            'url': 'https://sport.sky.it/motogp/2020/09/18/motogp-gp-emilia-romagna-misano-2020-prove-libere-diretta',
            'md5': '9c03b590b06e5952d8051f0e02b0feca',
            'info_dict': {
                'id': '616162',
                'ext': 'mp4',
                'title': 'MotoGP, GP Emilia Romagna: gli highlights delle prove libere',
                'thumbnail': 'https://videoplatform.sky.it/thumbnail/2020/09/18/1600441214452_hl-libere-motogp-misano2_5602634_thumbnail_1.jpg',
            }
        }
    ]

    def _real_extract(self, url):
        return self._get_formats(self._extract_video_id(url))


class SkyTg24ItIE(SkyItaliaBaseIE):
    IE_NAME = 'tg24.sky.it'
    _VALID_URL = r'https?://tg24\.sky\.it/.+?$'

    _TESTS = [
        {
            'url': 'https://tg24.sky.it/salute-e-benessere/2020/09/18/coronavirus-vaccino-ue-sanofi',
            'md5': 'caa25e62dadb529bc5e0b078da99f854',
            'info_dict': {
                'id': '615904',
                'ext': 'mp4',
                'title': 'Covid-19, al Buzzi di Milano tamponi drive-in per studenti',
                'thumbnail': 'https://videoplatform.sky.it/thumbnail/2020/09/17/1600351405841_error-coronavirus-al-buzzi-di-milano-tamponi_thumbnail_1.jpg',
            }
        }
    ]

    def _real_extract(self, url):
        return self._get_formats(self._extract_video_id(url))


class SkyArteItIE(SkyItaliaBaseIE):
    IE_NAME = 'arte.sky.it'
    _VALID_URL = r'https?://arte\.sky\.it/video/.+?$'

    _TESTS = [
        {
            'url': 'https://arte.sky.it/video/federico-fellini-maestri-cinema/',
            'md5': '2f22513a89f45142f2746f878d690647',
            'info_dict': {
                'id': '612888',
                'ext': 'mp4',
                'title': 'I maestri del cinema Federico Felini',
                'thumbnail': 'https://videoplatform.sky.it/thumbnail/2020/09/03/1599146747305_i-maestri-del-cinema-federico-felini_thumbnail_1.jpg',
            }
        }
    ]
    _TOKEN = 'LWk29hfiU39NNdq87ePeRach3nzTSV20o0lTv2001Cd'

    def _real_extract(self, url):
        return self._get_formats(self._extract_video_id(url), self._TOKEN)
