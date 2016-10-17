from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
)


class BandcampIE(InfoExtractor):
    _VALID_URL = r'https?://.*?\.bandcamp\.com/track/(?P<title>.*)'
    _TESTS = [{
        'url': 'http://youtube-dl.bandcamp.com/track/youtube-dl-test-song',
        'md5': 'c557841d5e50261777a6585648adf439',
        'info_dict': {
            'id': '1812978515',
            'ext': 'mp3',
            'title': "youtube-dl  \"'/\\\u00e4\u21ad - youtube-dl test song \"'/\\\u00e4\u21ad",
            'duration': 9.8485,
        },
        '_skip': 'There is a limit of 200 free downloads / month for the test song'
    }, {
        'url': 'http://benprunty.bandcamp.com/track/lanius-battle',
        'md5': '2b68e5851514c20efdff2afc5603b8b4',
        'info_dict': {
            'id': '2650410135',
            'ext': 'mp3',
            'title': 'Lanius (Battle)',
            'uploader': 'Ben Prunty Music',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        m_download = re.search(r'freeDownloadPage: "(.*?)"', webpage)
        if not m_download:
            m_trackinfo = re.search(r'trackinfo: (.+),\s*?\n', webpage)
            if m_trackinfo:
                json_code = m_trackinfo.group(1)
                data = json.loads(json_code)[0]

                formats = []
                for format_id, format_url in data['file'].items():
                    ext, abr_str = format_id.split('-', 1)
                    formats.append({
                        'format_id': format_id,
                        'url': self._proto_relative_url(format_url, 'http:'),
                        'ext': ext,
                        'vcodec': 'none',
                        'acodec': ext,
                        'abr': int_or_none(abr_str),
                    })

                self._sort_formats(formats)

                return {
                    'id': compat_str(data['id']),
                    'title': data['title'],
                    'formats': formats,
                    'duration': float_or_none(data.get('duration')),
                }
            else:
                raise ExtractorError('No free songs found')

        download_link = m_download.group(1)
        video_id = self._search_regex(
            r'(?ms)var TralbumData = .*?[{,]\s*id: (?P<id>\d+),?$',
            webpage, 'video id')

        download_webpage = self._download_webpage(download_link, video_id, 'Downloading free downloads page')
        # We get the dictionary of the track from some javascript code
        all_info = self._parse_json(self._search_regex(
            r'(?sm)items: (.*?),$', download_webpage, 'items'), video_id)
        info = all_info[0]
        # We pick mp3-320 for now, until format selection can be easily implemented.
        mp3_info = info['downloads']['mp3-320']
        # If we try to use this url it says the link has expired
        initial_url = mp3_info['url']
        m_url = re.match(
            r'(?P<server>http://(.*?)\.bandcamp\.com)/download/track\?enc=mp3-320&fsig=(?P<fsig>.*?)&id=(?P<id>.*?)&ts=(?P<ts>.*)$',
            initial_url)
        # We build the url we will use to get the final track url
        # This url is build in Bandcamp in the script download_bunde_*.js
        request_url = '%s/statdownload/track?enc=mp3-320&fsig=%s&id=%s&ts=%s&.rand=665028774616&.vrs=1' % (m_url.group('server'), m_url.group('fsig'), video_id, m_url.group('ts'))
        final_url_webpage = self._download_webpage(request_url, video_id, 'Requesting download url')
        # If we could correctly generate the .rand field the url would be
        # in the "download_url" key
        final_url = self._proto_relative_url(self._search_regex(
            r'"retry_url":"(.+?)"', final_url_webpage, 'final video URL'), 'http:')

        return {
            'id': video_id,
            'title': info['title'],
            'ext': 'mp3',
            'vcodec': 'none',
            'url': final_url,
            'thumbnail': info.get('thumb_url'),
            'uploader': info.get('artist'),
        }


class BandcampAlbumIE(InfoExtractor):
    IE_NAME = 'Bandcamp:album'
    _VALID_URL = r'https?://(?:(?P<subdomain>[^.]+)\.)?bandcamp\.com(?:/album/(?P<album_id>[^?#]+)|/?(?:$|[?#]))'

    _TESTS = [{
        'url': 'http://blazo.bandcamp.com/album/jazz-format-mixtape-vol-1',
        'playlist': [
            {
                'md5': '39bc1eded3476e927c724321ddf116cf',
                'info_dict': {
                    'id': '1353101989',
                    'ext': 'mp3',
                    'title': 'Intro',
                }
            },
            {
                'md5': '1a2c32e2691474643e912cc6cd4bffaa',
                'info_dict': {
                    'id': '38097443',
                    'ext': 'mp3',
                    'title': 'Kero One - Keep It Alive (Blazo remix)',
                }
            },
        ],
        'info_dict': {
            'title': 'Jazz Format Mixtape vol.1',
            'id': 'jazz-format-mixtape-vol-1',
            'uploader_id': 'blazo',
        },
        'params': {
            'playlistend': 2
        },
        'skip': 'Bandcamp imposes download limits.'
    }, {
        'url': 'http://nightbringer.bandcamp.com/album/hierophany-of-the-open-grave',
        'info_dict': {
            'title': 'Hierophany of the Open Grave',
            'uploader_id': 'nightbringer',
            'id': 'hierophany-of-the-open-grave',
        },
        'playlist_mincount': 9,
    }, {
        'url': 'http://dotscale.bandcamp.com',
        'info_dict': {
            'title': 'Loom',
            'id': 'dotscale',
            'uploader_id': 'dotscale',
        },
        'playlist_mincount': 7,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader_id = mobj.group('subdomain')
        album_id = mobj.group('album_id')
        playlist_id = album_id or uploader_id
        webpage = self._download_webpage(url, playlist_id)
        tracks_paths = re.findall(r'<a href="(.*?)" itemprop="url">', webpage)
        if not tracks_paths:
            raise ExtractorError('The page doesn\'t contain any tracks')
        entries = [
            self.url_result(compat_urlparse.urljoin(url, t_path), ie=BandcampIE.ie_key())
            for t_path in tracks_paths]
        title = self._search_regex(
            r'album_title\s*:\s*"(.*?)"', webpage, 'title', fatal=False)
        return {
            '_type': 'playlist',
            'uploader_id': uploader_id,
            'id': playlist_id,
            'title': title,
            'entries': entries,
        }
