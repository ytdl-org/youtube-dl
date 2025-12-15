# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    merge_dicts,
    ExtractorError,
)

"""
The extractor can download free videos from https://player.pl
The code is done from scratch, although 
the original idea and _REQUEST_VIDEO_URL is borrowed from 
https://github.com/zacny/voddownloader/
"""


class PlayerPlIE(InfoExtractor):
    IE_NAME = 'TVN'
    IE_DESC = 'Polska komercyjna stacja telewizyjna'
    _VALID_URL = r'https?://player\.pl/.*,(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'https://player.pl/programy-online/projekt-lady-odcinki,4554/odcinek-12,S05E12,186499',
            'info_dict': {
                'id': '186499',
                'ext': 'mp4',
                'title': 'Projekt Lady-S05E12',
                'description': 'md5:b322b3929f4e00bca010fe646122795a'
            }
        },
        {
            'url': 'https://player.pl/filmy-online/kino-2020---uszy-zyrafy,178673',
            'info_dict': {
                'id': '178673',
                'ext': 'mp4',
                'title': u'KINO 2020 - Uszy \u017byrafy-S00E00',
                'description': 'md5:852f5196a2304a3d941c1716ca71f1de'
            }
        }
    ]
    _REQUEST_VIDEO_URL = r'https://player.pl/api/?platform=ConnectedTV&terminal=Panasonic&format=json' \
                         '&authKey=064fda5ab26dc1dd936f5c6e84b7d3c2&v=3.1&m=getItem&id={videoid}'
    _SERIES_URL_RE = r'https?://player.pl/.*-odcinki,(?P<id>[0-9]+)'
    _SERIES_EPISODE_URL_RE = r'https?://player.pl/.*-odcinki,[0-9]+/odcinek-.*,(?P<id>[0-9]+)'
    _FILM_URL_RE = r'https?:\/\/player.pl\/.*(?<!-odcinki),(?P<id>[0-9]+)'
    _FORMATS_QUALITY_COMMON = {"ext": "mp4",
                               "format_id": "mp4_h2644_aac",
                               "acodec": "aac",
                               "fps": 25,
                               "vcodec": "h264",
                               "container": "mp4",
                               "language": "pl"
                               }
    _FORMATS_QUALITY = [
        (r'Bardzo niska', {"width": 320, "height": 240, "tbr": 238}),
        (r'Niska', {"width": 512, "height": 384, "tbr": 417}),
        (r'.*rednia', {"width": 640, "height": 480, "tbr": 596}),
        (r'Standard', {"width": 720, "height": 576, "tbr": 794}),
        (r'Wysoka', {"width": 720, "height": 576, "tbr": 1191}),
        (r'Bardzo wysoka', {"width": 1280, "height": 720, "tbr": 1786}),
        (r'HD', {"width": 1280, "height": 720, "tbr": 2776})
    ]

    def __get_format(self, fname):
        for i, x in enumerate(self._FORMATS_QUALITY):
            if re.match(x[0], fname):
                return i, merge_dicts(x[1], self._FORMATS_QUALITY_COMMON)
        self._downloader.report_warning("Unknown format '{}'".format(fname))
        return None

    def __extract_single_url(self, video_id):
        info = self._download_json(self._REQUEST_VIDEO_URL.format(videoid=video_id), video_id).get("item")
        formats = []
        for vfm in info.get("videos").get("main").get("video_content"):
            fm = self.__get_format(vfm.get("profile_name"))
            if fm is not None:
                fm[1].update({"url": vfm.get("url")})
                formats.append(fm)
        formats.sort()
        formats = [x[1] for x in formats]
        title = info.get("title")
        if title is None or title == '':
            title = "{}-S{:02d}E{:02d}".format(info.get("serie_title"), info.get("season"), info.get("episode"))

        return {
            'id': "id" + video_id,
            'title': title,
            'display_id': info.get("id"),
            'description': info.get("lead"),
            'duration': parse_duration(info.get('run_time')),
            'formats': formats,
            'series': info.get("serie_title"),
            'season': info.get("season_title"),
            'season_number': info.get("season"),
            'episode': info.get("episode_title"),
            'episode_number': info.get("episode"),
        }

    def __extract_series(self, video_id):
        int_video_resp = self._download_json(
            r'https://player.pl/playerapi/item/translate', None,
            query={
                "programId": video_id,
                "4K": "true",
                "platform": "BROWSER"
            })

        if int_video_resp.get('code') == "VOD_NOT_EXISTS" or str(int_video_resp.get("externalProgramId")) != video_id:
            raise ExtractorError('%s said: Video is not exists. Please check the URL' % self.IE_NAME, expected=True)

        int_prg_id = int(int_video_resp.get('id'))

        vod_prefix = r'https://player.pl/playerapi/product/vod/serial/'

        seasons = self._download_json(
            vod_prefix + r'{}/season/list'.format(int_prg_id), None,
            query={
                '4K': True,
                'platform': 'BROWSER'
            })
        seasons.sort(key=lambda k: k['number'])
        for sz in seasons:
            sid = sz.get("id")
            sn = sz.get('number')
            eps = self._download_json(
                vod_prefix + r'{prgid}/season/{sid}/episode/list'.format(prgid=int_prg_id, sid=sid), None,
                query={
                    '4K': True,
                    'platform': 'BROWSER'
                })
            lst = []
            for e in eps:
                if e["type"] == "EPISODE" and e["season"]["id"] == sid:
                    lst.append((sn, e.get("episode"), e.get("externalArticleId")))

            lst.sort()
            result = []
            for l in lst:
                rs = self.__extract_single_url(str(l[2]))
                if rs["formats"] is not None and len(rs["formats"]) > 0:
                    result.append(rs)
                else:
                    self._downloader.report_warning("Video '{}' is unavailable.".format(rs["title"]))

        s_info = self._download_json(
            vod_prefix + r'{}'.format(int_prg_id), None,
            query={
                '4K': True,
                'platform': 'BROWSER'
            })

        return self.playlist_result(result, playlist_id=video_id,
                                    playlist_title=s_info["title"], playlist_description=s_info["lead"])

    def _real_extract(self, url):
        for m in [re.match(self._SERIES_EPISODE_URL_RE, url), re.match(self._FILM_URL_RE, url)]:
            if m:
                return self.__extract_single_url(m.group("id"))

        m = re.match(self._SERIES_URL_RE, url)
        if m:
            return self.__extract_series(m.group("id"))

        return None
