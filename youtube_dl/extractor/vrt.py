# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
)


class VRTIE(InfoExtractor):
    IE_DESC = 'deredactie.be, sporza.be, cobra.be and cobra.canvas.be'
    _VALID_URL = r'https?://(?:deredactie|sporza|cobra(?:\.canvas)?)\.be/cm/(?:[^/]+/)+(?P<id>[^/]+)/*'
    _TESTS = [
        # deredactie.be
        {
            'url': 'http://deredactie.be/cm/vrtnieuws/videozone/programmas/journaal/EP_141025_JOL',
            'md5': '4cebde1eb60a53782d4f3992cbd46ec8',
            'info_dict': {
                'id': '2129880',
                'ext': 'flv',
                'title': 'Het journaal L - 25/10/14',
                'description': None,
                'timestamp': 1414271750.949,
                'upload_date': '20141025',
                'duration': 929,
            },
            'skip': 'HTTP Error 404: Not Found',
        },
        # sporza.be
        {
            'url': 'http://sporza.be/cm/sporza/videozone/programmas/extratime/EP_141020_Extra_time',
            'md5': '11f53088da9bf8e7cfc42456697953ff',
            'info_dict': {
                'id': '2124639',
                'ext': 'flv',
                'title': 'Bekijk Extra Time van 20 oktober',
                'description': 'md5:83ac5415a4f1816c6a93f8138aef2426',
                'timestamp': 1413835980.560,
                'upload_date': '20141020',
                'duration': 3238,
            },
            'skip': 'HTTP Error 404: Not Found',
        },
        # cobra.be
        {
            'url': 'http://cobra.be/cm/cobra/videozone/rubriek/film-videozone/141022-mv-ellis-cafecorsari',
            'md5': '78a2b060a5083c4f055449a72477409d',
            'info_dict': {
                'id': '2126050',
                'ext': 'flv',
                'title': 'Bret Easton Ellis in Café Corsari',
                'description': 'md5:f699986e823f32fd6036c1855a724ee9',
                'timestamp': 1413967500.494,
                'upload_date': '20141022',
                'duration': 661,
            },
            'skip': 'HTTP Error 404: Not Found',
        },
        {
            # YouTube video
            'url': 'http://deredactie.be/cm/vrtnieuws/videozone/nieuws/cultuurenmedia/1.2622957',
            'md5': 'b8b93da1df1cea6c8556255a796b7d61',
            'info_dict': {
                'id': 'Wji-BZ0oCwg',
                'ext': 'mp4',
                'title': 'ROGUE ONE: A STAR WARS STORY Official Teaser Trailer',
                'description': 'md5:8e468944dce15567a786a67f74262583',
                'uploader': 'Star Wars',
                'uploader_id': 'starwars',
                'upload_date': '20160407',
            },
            'add_ie': ['Youtube'],
        },
        {
            'url': 'http://cobra.canvas.be/cm/cobra/videozone/rubriek/film-videozone/1.2377055',
            'info_dict': {
                'id': '2377055',
                'ext': 'mp4',
                'title': 'Cafe Derby',
                'description': 'Lenny Van Wesemael debuteert met de langspeelfilm Café Derby. Een waar gebeurd maar ook verzonnen verhaal.',
                'upload_date': '20150626',
                'timestamp': 1435305240.769,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'data-video-id="([^"]+)_[^"]+"', webpage, 'video id', fatal=False)

        src = self._search_regex(
            r'data-video-src="([^"]+)"', webpage, 'video src', default=None)

        video_type = self._search_regex(
            r'data-video-type="([^"]+)"', webpage, 'video type', default=None)

        if video_type == 'YouTubeVideo':
            return self.url_result(src, 'Youtube')

        formats = []

        mobj = re.search(
            r'data-video-iphone-server="(?P<server>[^"]+)"\s+data-video-iphone-path="(?P<path>[^"]+)"',
            webpage)
        if mobj:
            formats.extend(self._extract_m3u8_formats(
                '%s/%s' % (mobj.group('server'), mobj.group('path')),
                video_id, 'mp4', m3u8_id='hls', fatal=False))

        if src:
            formats = self._extract_wowza_formats(src, video_id)
            if 'data-video-geoblocking="true"' not in webpage:
                for f in formats:
                    if f['url'].startswith('rtsp://'):
                        http_format = f.copy()
                        http_format.update({
                            'url': f['url'].replace('rtsp://', 'http://').replace('vod.', 'download.').replace('/_definst_/', '/').replace('mp4:', ''),
                            'format_id': f['format_id'].replace('rtsp', 'http'),
                            'protocol': 'http',
                        })
                        formats.append(http_format)

        if not formats and 'data-video-geoblocking="true"' in webpage:
            self.raise_geo_restricted('This video is only available in Belgium')

        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = float_or_none(self._search_regex(
            r'data-video-sitestat-pubdate="(\d+)"', webpage, 'timestamp', fatal=False), 1000)
        duration = float_or_none(self._search_regex(
            r'data-video-duration="(\d+)"', webpage, 'duration', fatal=False), 1000)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }


class SporzaIE(InfoExtractor):
    _VALID_URL = r'https?://sporza\.be/nl/(?:[^/]+/)+(?P<id>[^/]+)/*'
    _TESTS = [{
        'url': 'https://sporza.be/nl/2018/08/20/israel-is-geen-partij-voor-de-yellow-tigers/',
        'md5': 'b13b66a4b95daccf2ada6b3ca94109c6',
        'info_dict': {
            'id': 'vid-f3d9b1c6-5c8b-414c-a2ba-9c895e50c890',
            'ext': 'mp4',
            'title': 'Israël is geen partij voor de Yellow Tigers',
            'description': 'Israël is geen partij voor de Yellow Tigers',
            'thumbnail': r're:^https?://images.vrt.be/.*\.jpg$',
        },
    },
        {
            'url': 'https://sporza.be/nl/2018/07/29/de-tour-van-thomas/',
            'md5': '267213350047577b614ee9804dd5b0c8',
            'info_dict': {
                'id': 'vid-155c6577-addc-48d3-b86f-1d66f19d6bcc',
                'ext': 'mp4',
                'title': 'De Tour van Thomas',
                'description': 'De Tour van Thomas',
                'thumbnail': r're:^https?://images.vrt.be/.*\.jpg$',
            },
    }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'data-videoid=\"([^\"]+)\"', webpage, 'video id', fatal=True)
        publication_id = self._search_regex(
            r'data-publicationid=\"([^\"]+)\"', webpage, 'publication id', fatal=True)
        api_url = self._search_regex(
            r'data-mediaapiurl=\"([^\"]+)\"', webpage, 'api url',
            default="https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1")
        video_client = self._search_regex(
            r'data-client=\"([^\"]+)\"', webpage, 'video client', default="sporza")

        # Get a player token
        vrtPlayerToken = self._download_json(
            "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/tokens",
            video_id, headers={"content-type": "application/json"}, data={}).get(
            "vrtPlayerToken")  # Default content type results in 415, correct content-type from: https://github.com/pietje666/plugin.video.vrt.nu/issues/21

        src = api_url + "/videos/" + publication_id + "$" + video_id + "/?vrtPlayerToken=" + vrtPlayerToken + "&client=" + video_client
        meta = self._download_json(src, video_id)

        targetUrl = next((x for x in meta["targetUrls"] if x["type"]=="hls")).get("url")
        formats = self._extract_m3u8_formats(targetUrl, video_id, "mp4")

        return {
            'id': video_id,
            'title': meta.get('title') or self._og_search_title(webpage),
            'description': meta.get('shortDescription'),
            'thumbnail': meta.get('posterImageUrl'),
            'duration': meta.get('duration'),
            'formats': formats,
        }
