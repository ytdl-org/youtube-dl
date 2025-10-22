# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    dict_get,
    get_element_by_class,
    js_to_json,
    parse_duration,
    parse_iso8601,
    str_or_none,
    try_get,
)
from ..compat import (
    compat_etree_Element,
    compat_etree_fromstring,
    compat_str,
    compat_xpath,
)


class MegaphoneIE(InfoExtractor):
    IE_NAME = 'megaphone.fm'
    IE_DESC = 'megaphone.fm embedded players'
    _PLAYER_URL_TEMPL = 'https://player.megaphone.fm/%s'
    _VALID_URL_TEMPL = _PLAYER_URL_TEMPL.replace('.', r'\.')
    _VALID_URL = _VALID_URL_TEMPL % r'(?P<id>[A-Z0-9]+)'
    _JSON_URL_TEMPL = _PLAYER_URL_TEMPL % 'playlist/episode/%s'
    _TESTS = [{
        'url': 'https://player.megaphone.fm/GLT9749789991',
        'md5': '4816a0de523eb3e972dc0dda2c191f96',
        'info_dict': {
            'id': 'GLT9749789991',
            'ext': 'mp3',
            'title': '#97 What Kind Of Idiot Gets Phished?',
            'thumbnail': r're:^https://.*\.png(?:\?.+)?$',
            'duration': 2013.36,
            'uploader': 'Reply All',
            'upload_date': '20170518',
            'timestamp': 1495101600,
            'description': 'md5:8fc2ba1da0efb099ef928df127358a90',
        },
    }]

    def _old_real_extract(self, url, video_id):
        """version for pages before React-ification"""
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_property('audio:title', webpage)
        author = self._og_search_property('audio:artist', webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        episode_json = self._search_regex(r'(?s)var\s+episode\s*=\s*(\{.+?\});', webpage, 'episode JSON')
        episode_data = self._parse_json(episode_json, video_id, js_to_json)
        video_url = self._proto_relative_url(episode_data['mediaUrl'], 'https:')

        formats = [{
            'url': video_url,
        }]

        return {
            'id': video_id,
            'thumbnail': thumbnail,
            'title': title,
            'author': author,
            'duration': episode_data.get('duration'),
            'formats': formats,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        episode_json = self._download_json(self._JSON_URL_TEMPL % video_id, video_id, fatal=False)
        if episode_json is False:
            # probably, no pages match the old structure, but try anyway
            return self._old_real_extract(url, video_id)
        entries = []
        for e in try_get(episode_json, lambda x: x['episodes'], list) or []:
            title = try_get(e, lambda x: x['title'], compat_str)
            if not title:
                continue
            video_url = dict_get(e, ('episodeUrlHRef', 'audioURL'))
            if not video_url:
                continue
            entry = {
                'id': e.get('UID') or video_id,
                'title': title,
                'description': clean_html(e.get('summary')),
                'alt_title': e.get('subtitle'),
                'formats': [{'url': video_url}],
                'thumbnail': e.get('imageUrl'),
                'duration': parse_duration(e.get('duration')),
                'timestamp': parse_iso8601(e.get('pubDate')),
            }
            uploader = episode_json.get('podcastTitle')
            if uploader:
                entry['uploader'] = uploader
                entry['author'] = uploader
            entries.append(entry)
        if entries:
            if len(entries) == 1:
                return entries[0]
            return self.playlist_result(entries, playlist_id=video_id, playlist_title=episode_json.get('podcastTitle'))

    @classmethod
    def _extract_urls(cls, webpage):
        return [m[0] for m in re.findall(
            r'<iframe[^>]*?\ssrc=["\'](%s)' % cls._VALID_URL, webpage)]


class MegaphoneEpisodeIE(MegaphoneIE):
    IE_NAME = 'megaphone.fm:episode'
    IE_DESC = 'megaphone.fm episode'
    _VALID_URL_TEMPL = r'https://playlist\.megaphone\.fm/?%s'
    _VALID_URL = _VALID_URL_TEMPL % r'\?e=(?P<id>[A-Z0-9]+)'
    _JSON_URL_TEMPL = MegaphoneIE._PLAYER_URL_TEMPL % 'playlist/episode/%s'
    _TESTS = [{
        'url': 'https://playlist.megaphone.fm/?e=PAN7405681599',
        'md5': '7fa866c3af93caac7e13a579c183f6ab',
        'info_dict': {
            'id': 'PAN7405681599',
            'ext': 'mp3',
            'title': 'Nirvana - Nevermind: 30 Years Later with Danny Goldberg',
            'thumbnail': r're:^https://.*\.jpe?g(?:\?.+)?$',
            'duration': 3576.94,
            'uploader': 'Cobras & Fire: Comedy / Rock Talk Show',
            'upload_date': '20210810',
            'timestamp': 1628578800,
            'description': 'md5:8f5623a8b22d3be4420c4570d0e36b69',
        },
    }]


class MegaphonePlaylistIE(MegaphoneEpisodeIE):
    IE_NAME = 'megaphone.fm:playlist'
    IE_DESC = 'megaphone.fm playlist'
    _VALID_URL = MegaphoneEpisodeIE._VALID_URL_TEMPL % r'\?p=(?P<id>[A-Z0-9]+)'
    _JSON_URL_TEMPL = MegaphoneIE._PLAYER_URL_TEMPL % 'playlist/%s'
    _TESTS = [{
        'url': 'https://playlist.megaphone.fm/?p=DEM6640968282',
        'info_dict': {
            'id': 'DEM6640968282',
            'title': 'Lightbulb Productions',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://playlist.megaphone.fm/?p=DEM6640968282',
        'md5': '71fbb6616c75aa2cc972e978683dffd4',
        'info_dict': {
            'id': 'DEM6640968282',
            'ext': 'mp3',
            'title': 'Open Source World',
            'thumbnail': r're:^https://.*\.jpe?g(?:\?.+)?$',
            'duration': 754.38,
            'uploader': 'Lightbulb Productions',
            'upload_date': '20200602',
            'timestamp': 1591070400,
            'description': 'md5:a06a5a078c0d98bb023626615fb1432d',
        },
        'params': {
            'noplaylist': True,
        },
    }]

    def _real_extract(self, url):
        entries = super(MegaphonePlaylistIE, self)._real_extract(url)
        if entries:
            noplaylist = self._downloader.params.get('noplaylist')
            if noplaylist:
                self.to_screen('Downloading just the first episode because of --no-playlist')
                return entries['entries'][0]
        return entries


class MegaphoneChannelIE(MegaphoneIE):
    IE_NAME = 'megaphone.fm:channel'
    IE_DESC = 'megaphone.fm channel'
    _VALID_URL = r'https://cms\.megaphone\.fm/channel/(?P<id>[A-Z0-9]+)(?:\?selected=(?P<clip_id>[A-Z0-9]+))?'
    _TESTS = [{
        'url': 'https://cms.megaphone.fm/channel/ADL3707263633',
        'info_dict': {
            'id': 'ADL3707263633',
            'title': 'Pax Britannica',
            'description': 'md5:7b4002330ffe4abcb81d97ab9b56fede',
        },
        'playlist_mincount': 98,
    }, {
        'url': 'https://cms.megaphone.fm/channel/ADL3707263633?selected=ADL9449136081',
        'md5': '42901d1112c059a8de374046e0b1ed25',
        'info_dict': {
            'id': 'ADL9449136081',
            'title': '02.23 - Nolumus Leges Angliae Mutari',
            'description': 'md5:d35989ec81de7199b3020bc919ab7c0d',
            'ext': 'mp3',
            'thumbnail': r're:^https://.*\.png(?:\?.+)?$',
            'duration': 2470.09,
            'extractor_key': 'Megaphone',
            'upload_date': '20210711',
            'timestamp': 1625961600,
            'uploader': 'Pax Britannica',
        },
    }, {
        'url': 'https://cms.megaphone.fm/channel/ADL3707263633',
        'md5': '81156c760235d45a9133a9ea9ccbb7d0',
        'info_dict': {
            'id': 'ADL9716153485',
            'title': '02.24 - Give Unto Caesar His Due',
            'description': 'The First English Civil War begins.',
            'ext': 'mp3',
            'duration': 1860,
        },
        'params': {
            'noplaylist': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url).groupdict()
        video_id = mobj['id']
        # If clip is selected, dl that instead
        clip_id = mobj.get('clip_id')
        if clip_id:
            return self.url_result(self._PLAYER_URL_TEMPL % clip_id, ie='Megaphone', video_id=clip_id)
        webpage = self._download_webpage(url, video_id)
        # Useful information is split between a JS JSON.parse() call and
        # a <div class="public-ep-list>...</div> HTML element
        playlist_json = self._search_regex(
            r"var\s+playlist\s*=\s*JSON\.parse\s*\(\s*('[^<]+?')\s*\)\s*;",
            webpage, 'playlist JSON')
        # The data must be parsed twice: once for JSON.parse, once for Python
        playlist_json = self._parse_json(
            playlist_json, video_id,
            transform_source=lambda s: self._parse_json(s, video_id, transform_source=js_to_json))
        entries = []
        ep_list = None
        # Support --no-playlist to get the first item when no explicit selection
        noplaylist = self._downloader.params.get('noplaylist')
        for ep_num, episode in enumerate(playlist_json):
            ep_url = episode.get('mp3')
            ep_title = episode.get('title')
            ep_id = episode.get('uid')
            if not (ep_url and ep_id):
                continue
            entry = {
                'url': ep_url,
                'id': ep_id,
            }
            if ep_num == 0:
                # As there are items to process, initialise the public-ep-list
                ep_list = self._search_regex(
                    r'(?s)<div\s[^>]*?class\s*=\s*("|\')public-ep-list\1[^>]*>.*?(?P<ep_list><div\s[^>]*?id\s*=.+?</div>\s*</div>)\s*</div>',
                    webpage, 'episode list', default=None, group='ep_list')
                if ep_list:
                    # Although the page itself isn't well-formed as XML, the
                    # <div class="public-ep-list>...</div> HTML element is (apparently)
                    # So for "easy" extraction, make it into a compat_etree_Element
                    ep_list = '<?xml version="1.0" encoding="UTF-8"?><eplist>%s</eplist>' % ep_list
                    ep_list = ep_list.encode('utf-8')
                    ep_list = try_get(ep_list, compat_etree_fromstring, compat_etree_Element)
            if ep_list is not None:
                # Use the subset XPath syntax to extract the additional data (counted from 0)
                ep_info = ep_list.find(compat_xpath("div[@id='%d']" % ep_num))
                if ep_info is not None:
                    if not ep_title:
                        title = ep_info.find(compat_xpath(".//div[@class='ep-title']"))
                        if title:
                            ep_title = str_or_none(title.text)
                    description = ep_info.find(compat_xpath(".//div[@class='ep-summary']"))
                    if description is not None:
                        entry['description'] = str_or_none(description.text)
                    duration = ep_info.find(compat_xpath(".//div[@class='ep-duration']"))
                    if duration is not None:
                        entry['duration'] = parse_duration(duration.text)
            if not ep_title:
                continue
            entry['title'] = ep_title
            if ep_num == 0 and noplaylist:
                self.to_screen('Downloading just the first episode because of --no-playlist')
                return entry
            entries.append(entry)
        if entries:
            title = (self._og_search_property('audio:artist', webpage, default=None)
                     or get_element_by_class('title', webpage))
            description = get_element_by_class('summary', webpage)
            return self.playlist_result(entries, video_id, title, description)
