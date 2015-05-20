# encoding: utf-8
from __future__ import unicode_literals

import re
import json
import base64
import xml.etree.ElementTree

# Soompi uses the same subtitle encryption as crunchyroll
from .crunchyroll import CrunchyrollIE


class SoompiIE(CrunchyrollIE):
    IE_NAME = 'soompi'
    _VALID_URL = r'^https?://tv\.soompi\.com/en/watch/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://tv.soompi.com/en/watch/29235',
        'info_dict': {
            'id': '29235',
            'ext': 'mp4',
            'title': 'Episode 1096',
            'description': '2015-05-20'
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _get_episodes(self, webpage, episode_filter=None):
        episodes = json.loads(
            self._search_regex(r'\s+VIDEOS\s+= (\[.+?\]);', webpage, "episodes meta"))
        return [ep for ep in episodes if episode_filter is None or episode_filter(ep)]

    def _get_subtitles(self, video_id, show_format_xml):
        subtitles = {}
        subtitle_info_nodes = show_format_xml.findall('./{default}preload/subtitles/subtitle')
        subtitle_nodes = show_format_xml.findall('./{default}preload/subtitle')

        sub_langs = {}
        for i in subtitle_info_nodes:
            sub_langs[i.attrib["id"]] = i.attrib["title"]

        for s in subtitle_nodes:
            lang_code = sub_langs.get(s.attrib["id"], None)
            if lang_code is None:
                continue

            sub_id = int(s.attrib["id"])
            iv = base64.b64decode(s.find("iv").text)
            data = base64.b64decode(s.find("data").text)
            subtitle = self._decrypt_subtitles(data, iv, sub_id).decode('utf-8')
            sub_root = xml.etree.ElementTree.fromstring(subtitle)

            subtitles[lang_code] = [{
                'ext': 'srt', 'data': self._convert_subtitles_to_srt(sub_root)
            }, {
                'ext': 'ass', 'data': self._convert_subtitles_to_ass(sub_root)
            }]
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id, note="Downloading episode page",
            errnote="Video may not be available for your location")
        vid_formats = re.findall(r"\?quality=q([0-9]+)", webpage)

        show_meta = json.loads(
            self._search_regex(r'\s+var show = (\{.+?\});', webpage, "show meta"))
        episodes = self._get_episodes(
            webpage, episode_filter=lambda x: x['id'] == video_id)

        title = episodes[0]["name"]
        description = episodes[0]["description"]
        duration = int(episodes[0]["duration"])
        slug = show_meta["slug"]

        formats = []
        show_format_xml = None
        for vf in vid_formats:
            show_format_url = "http://tv.soompi.com/en/show/%s/%s-config.xml?mode=hls&quality=q%s" \
                              % (slug, video_id, vf)
            show_format_xml = self._download_xml(
                show_format_url, video_id, note="Downloading q%s show xml" % vf)
            avail_formats = self._extract_m3u8_formats(
                show_format_xml.find('./{default}preload/stream_info/file').text,
                video_id, ext="mp4", m3u8_id=vf, preference=int(vf))
            formats.extend(avail_formats)
        self._sort_formats(formats)

        subtitles = self.extract_subtitles(video_id, show_format_xml)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles
        }


class SoompiShowIE(SoompiIE):
    IE_NAME = 'soompi:show'
    _VALID_URL = r'^https?://tv\.soompi\.com/en/shows/(?P<id>[0-9a-zA-Z\-_]+)'
    _TESTS = [{
        'url': 'http://tv.soompi.com/en/shows/liar-game',
        'info_dict': {
            'id': 'liar-game',
            'title': 'Liar Game',
            'description': 'md5:52c02bce0c1a622a95823591d0589b66',
        },
        'playlist_count': 14,
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)

        webpage = self._download_webpage(url, show_id, note="Downloading show page")
        title = self._og_search_title(webpage).replace("SoompiTV | ", "")
        description = self._og_search_description(webpage)

        episodes = self._get_episodes(webpage)
        entries = []
        for ep in episodes:
            entries.append(self.url_result(
                'http://tv.soompi.com/en/watch/%s' % ep['id'], 'Soompi', ep['id']))

        return self.playlist_result(entries, show_id, title, description)
