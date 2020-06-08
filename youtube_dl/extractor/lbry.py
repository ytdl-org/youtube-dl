# coding: utf-8
from __future__ import unicode_literals

import re
import itertools
import json

from .common import InfoExtractor


class LBRYIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lbry\.tv/@(?P<uploader_url>[^/?#&]+:[0-9a-f]+)/(?P<title_url>[^/?#&]+:[0-9a-f]+)'
    _TEST = {
        'url': 'https://lbry.tv/@MimirsBrunnr:8/sunne-light-of-the-world-summer-solstice:6',
        'md5': '18e0cf991d0a9db3e23e979c20ed40a1',
        'info_dict': {
            'id': '62b95f07397a291d16e911ce7eb7c816a6992202',
            'ext': 'mp4',
            'title': 'Sunne, Light of the World (Summer Solstice)',
            'title_url': 'sunne-light-of-the-world-summer-solstice:6',
            'thumbnail': 'https://thumbnails.lbry.com/gtsvh8nQLHA',
            'uploader': 'Mimir\'s Brunnr',
            'uploader_url': 'MimirsBrunnr:8'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        uploader_url = mobj.group('uploader_url')
        title_url = mobj.group('title_url')

        webpage = self._download_webpage('https://lbry.tv/@%s/%s' % (uploader_url, title_url), uploader_url + '+' + title_url)
        webpage_uploader = self._download_webpage('https://lbry.tv/@%s' % uploader_url, uploader_url)

        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title', default=None) or \
            self._og_search_property('title', webpage)
        thumbnail = self._og_search_property('image', webpage)
        uploader = self._html_search_regex(r'<title>(.*?)</title>', webpage_uploader, 'uploader', default=None) or \
            self._og_search_property('title', webpage_uploader)

        embed_url = self._og_search_property('video', webpage, default=None) or \
            self._og_search_property('video:secure_url', webpage, default=None) or \
            self._og_search_property('twitter:player', webpage)

        video_id = embed_url.split('/')[-1]

        video_type = self._og_search_property('video:type', webpage)
        video_ext = video_type.replace('video/', '')

        format_url = embed_url.replace('lbry.tv/$/embed', 'player.lbry.tv/content/claims') + '/stream?download=1'
        formats = [{'ext': video_ext, 'url': format_url, 'vcodec': 'h264', 'acodec': 'aac'}]

        return {
            'id': video_id,
            'ext': video_ext,
            'title': title,
            'title_url': title_url,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_url': uploader_url,
            'formats': formats,
        }


class LBRYChannelIE(InfoExtractor):
    IE_NAME = 'lbry:channel'
    _VALID_URL = r'https?://(?:www\.)?lbry\.tv/@(?P<id>[^/?#&]+:[0-9a-f]+)'
    _TESTS = [{
        'url': 'https://lbry.tv/@TheLinuxGamer:f',
        'info_dict': {
            'id': '@TheLinuxGamer:feb61536c007cdf4faeeaab4876cb397feaf6b51',
            'title': 'lbry @TheLinuxGamer',
        },
        'playlist_mincount': 500,
    }]
    _BASE_URL_TEMPL = 'https://lbry.tv/%s'

    def _extract_list_title(self, webpage):
        return self._TITLE or self._html_search_regex(
            self._TITLE_RE, webpage, 'list title', fatal=False)

    def _title_and_entries(self, channel_id, base_url):
        claim_id = channel_id.split(":")[-1]
        for pagenum in itertools.count(1):
            data = {"jsonrpc": "2.0",
                    "method": "claim_search",
                    "params": {
                        "page_size": 50,
                        "page": pagenum,
                        "no_totals": True,
                        "channel_ids": [claim_id],
                        "not_channel_ids": [],
                        "order_by": ["release_time"],
                        "include_purchase_receipt": True
                    },
                    "id": 1591611001494}

            clips = self._download_json("https://api.lbry.tv/api/v1/proxy?m=claim_search", None,
                                        headers={'Content-Type': 'application/json-rpc', },
                                        data=json.dumps(data).encode())["result"]["items"]

            if pagenum == 1:
                yield "lbry " + clips[0]["signing_channel"]['name']

            for clip in clips:
                # the permanent_url is the lbry:// protocol url:
                video_id = clip["permanent_url"][7:].replace("#", ":")

                yield self.url_result("https://lbry.tv/%s/%s" % (channel_id, video_id),
                                      LBRYIE.ie_key(), video_id=video_id)
            if len(clips) == 0:
                break

    def _extract_videos(self, list_id, base_url):
        title_and_entries = self._title_and_entries(list_id, base_url)
        list_title = next(title_and_entries)
        return self.playlist_result(title_and_entries, list_id, list_title)

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        webpage = self._download_webpage('https://lbry.tv/@%s' % (channel_id), channel_id)
        real_channel_id = self._og_search_url(webpage).split("/")[-1]
        return self._extract_videos(real_channel_id, self._BASE_URL_TEMPL % real_channel_id)
