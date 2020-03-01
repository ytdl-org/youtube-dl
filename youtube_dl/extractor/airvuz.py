# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    ExtractorError,
    unified_timestamp
)

import re


class AirVuzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?airvuz\.com/video/(?P<display_id>.+)\?id=(?P<id>.+)'
    _TESTS = [
        {
            'url': 'https://www.airvuz.com/video/1-pack-before-the-thunderstorm?id=5d3c10176c32ae7ddc7cab29',
            'info_dict': {
                'id': '5d3c10176c32ae7ddc7cab29',
                'display_id': '1-pack-before-the-thunderstorm',
                'title': '1 pack before the thunderstorm',
                'ext': 'mp4',
                'thumbnail': r're:^https?://cdn.airvuz.com/image/drone-video-thumbnail\?image=airvuz-drone-video/43a6dd35ec08457545655905d638ea58/4c71ed0d6e1d93a06a0f3a053097af85.45.*',
                'timestamp': 1564217367,
                'upload_date': '20190727',
                'uploader': 'Menga FPV',
                'uploader_id': 'menga-fpv',
                'uploader_url': 'https://www.airvuz.com/user/menga-fpv',
                'description': 'md5:13e8079235de737142d475f0b4058869',
            },
            'params': {
                'format': 'video-1'
            }
        },
        # No MPD
        {
            'url': 'https://www.airvuz.com/video/An-Imaginary-World?id=599e85c49282a717c50f2f7a',
            'info_dict': {
                'id': '599e85c49282a717c50f2f7a',
                'display_id': 'An-Imaginary-World',
                'title': 'An Imaginary World',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg',
                'timestamp': 1503561156,
                'upload_date': '20170824',
                'uploader': 'Tobias Hägg',
                'uploader_id': 'tobias-hägg',
                'uploader_url': 'https://www.airvuz.com/user/tobias-hägg',
                'description': 'md5:176b43a79a0a19d592c0261d9c0a48c7',
            }
        },
        # Emojis in the URL, title and description
        {
            'url': 'https://www.airvuz.com/video/Cinematic-FPV-Flying-at-a-Cove-%F0%9F%8C%8A%F0%9F%8C%8A%F0%9F%8C%8A-The-rocks-waves-and-seaweed%F0%9F%98%8D?id=5d3db133ec63bf7e65c2226e',
            'info_dict': {
                'id': '5d3db133ec63bf7e65c2226e',
                'display_id': 'Cinematic-FPV-Flying-at-a-Cove-🌊🌊🌊-The-rocks-waves-and-seaweed😍',
                'title': 'Cinematic FPV Flying at a Cove! 🌊🌊🌊 The rocks, waves, and seaweed😍!',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg',
                'timestamp': 1564324147,
                'upload_date': '20190728',
                'uploader': 'Mako Reactra',
                'uploader_id': 'mako-reactra',
                'uploader_url': 'https://www.airvuz.com/user/mako-reactra',
                'description': 'md5:ac91310ff7c2de26a0f1e8e8caae2ee6'
            },
            'params': {
                'format': 'video-1'
            }
        },
    ]

    def _extract_og_property(self, prop, html, fatal=False):
        return self._html_search_regex(r'<meta[^>]+?(?:name|property)=(?:\'og:%s\'|"og:%s"|og:%s)[^>]+?content=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))' % (prop, prop, prop), html, prop, fatal=fatal, default=None)

    def _real_extract(self, url):
        groups = re.match(self._VALID_URL, url)
        video_id = groups.group('id')
        display_id = compat_urllib_parse_unquote(groups.group('display_id'))

        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        title = self._og_search_title(webpage) or self._html_search_meta('twitter:title', webpage, fatal=True)
        thumbnail = self._og_search_thumbnail(webpage) or self._html_search_meta('twitter:image', webpage, fatal=False)
        description = self._og_search_description(webpage)
        timestamp = unified_timestamp(self._extract_og_property('updated_time', webpage, fatal=False))
        uploader = self._html_search_regex(r'class=(?:\'img-circle\'|"img-circle"|img-circle)[^>]+?alt=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))', webpage, 'uploader', fatal=False, default=None)

        uploader_id = None
        uploader_url = None
        uploader_info = re.search(r'(?P<url>https?://(?:www\.)?airvuz\.com/user/(?P<id>[^>]+))', webpage)
        if uploader_info is not None:
            uploader_id = uploader_info.group('id')
            uploader_url = uploader_info.group('url')

        video_url = self._extract_og_property('video:url', webpage, fatal=True)

        formats = []
        mpd_info = False

        result = re.match(r'https?://cdn\.airvuz\.com/drone-video/(?P<id>.+)/', video_url)
        if result:
            mpd_id = result.group('id')
            mpd_pattern = 'https://www.airvuz.com/drone-video/%s/dash/%s_dash.mpd' % (mpd_id, mpd_id)

            try:
                # Try to get mpd file
                mpd_formats = self._extract_mpd_formats(mpd_pattern, video_id, fatal=True)
                if mpd_formats:
                    # VIDEO-1 has always the highest quality
                    for format in reversed(mpd_formats):
                        format["format_id"] = format["format_id"].lower()
                        formats.append(format)

                    mpd_info = True

            except ExtractorError:
                pass

        if mpd_info is False:
            try:
                # Some videos don't have MPD information
                # Use undocumented API to get the formats
                meta = self._download_json('https://www.airvuz.com/api/videos/%s?type=dynamic' % video_id, video_id, fatal=True)
                if meta:
                    info_res = meta.get('data')

                    for res in reversed(info_res.get('resolutions')):
                        video_url = res.get('src')
                        if not video_url:
                            continue

                        # URL is a relative path
                        video_url = 'https://www.airvuz.com/%s' % video_url

                        formats.append({
                            'url': video_url,
                            'format_id': res.get('label'),
                        })

            except ExtractorError:
                #  Fallback to original video
                self.report_warning('Unable to extract formats')
                self.to_screen('%s: Extracting original video' % video_id)

                if video_url:
                    format_id = video_url.split("-")[-1].split(".")[0]
                    if len(format_id) <= 2:
                        # Format can't be induced from the filename
                        format_id = None

                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                    })
                else:
                    raise ExtractorError('Unable to extract video data')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
        }
