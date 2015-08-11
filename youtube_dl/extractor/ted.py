from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor

from ..compat import compat_str
from ..utils import int_or_none


class TEDIE(InfoExtractor):
    IE_NAME = 'ted'
    _VALID_URL = r'''(?x)
        (?P<proto>https?://)
        (?P<type>www|embed(?:-ssl)?)(?P<urlmain>\.ted\.com/
        (
            (?P<type_playlist>playlists(?:/\d+)?) # We have a playlist
            |
            ((?P<type_talk>talks)) # We have a simple talk
            |
            (?P<type_watch>watch)/[^/]+/[^/]+
        )
        (/lang/(.*?))? # The url may contain the language
        /(?P<name>[\w-]+) # Here goes the name and then ".html"
        .*)$
        '''
    _TESTS = [{
        'url': 'http://www.ted.com/talks/dan_dennett_on_our_consciousness.html',
        'md5': 'fc94ac279feebbce69f21c0c6ee82810',
        'info_dict': {
            'id': '102',
            'ext': 'mp4',
            'title': 'The illusion of consciousness',
            'description': ('Philosopher Dan Dennett makes a compelling '
                            'argument that not only don\'t we understand our own '
                            'consciousness, but that half the time our brains are '
                            'actively fooling us.'),
            'uploader': 'Dan Dennett',
            'width': 854,
            'duration': 1308,
        }
    }, {
        'url': 'http://www.ted.com/watch/ted-institute/ted-bcg/vishal-sikka-the-beauty-and-power-of-algorithms',
        'md5': '226f4fb9c62380d11b7995efa4c87994',
        'info_dict': {
            'id': 'vishal-sikka-the-beauty-and-power-of-algorithms',
            'ext': 'mp4',
            'title': 'Vishal Sikka: The beauty and power of algorithms',
            'thumbnail': 're:^https?://.+\.jpg',
            'description': 'Adaptive, intelligent, and consistent, algorithms are emerging as the ultimate app for everything from matching consumers to products to assessing medical diagnoses. Vishal Sikka shares his appreciation for the algorithm, charting both its inherent beauty and its growing power.',
        }
    }, {
        'url': 'http://www.ted.com/talks/gabby_giffords_and_mark_kelly_be_passionate_be_courageous_be_your_best',
        'info_dict': {
            'id': '1972',
            'ext': 'mp4',
            'title': 'Be passionate. Be courageous. Be your best.',
            'uploader': 'Gabby Giffords and Mark Kelly',
            'description': 'md5:5174aed4d0f16021b704120360f72b92',
            'duration': 1128,
        },
    }, {
        'url': 'http://www.ted.com/playlists/who_are_the_hackers',
        'info_dict': {
            'id': '10',
            'title': 'Who are the hackers?',
        },
        'playlist_mincount': 6,
    }, {
        # contains a youtube video
        'url': 'https://www.ted.com/talks/douglas_adams_parrots_the_universe_and_everything',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': '_ZG8HBuDjgc',
            'ext': 'mp4',
            'title': 'Douglas Adams: Parrots the Universe and Everything',
            'description': 'md5:01ad1e199c49ac640cb1196c0e9016af',
            'uploader': 'University of California Television (UCTV)',
            'uploader_id': 'UCtelevision',
            'upload_date': '20080522',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # YouTube video
        'url': 'http://www.ted.com/talks/jeffrey_kluger_the_sibling_bond',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': 'aFBIPO-P7LM',
            'ext': 'mp4',
            'title': 'The hidden power of siblings: Jeff Kluger at TEDxAsheville',
            'description': 'md5:3d7a4f50d95ca5dd67104e2a20f43fe1',
            'uploader': 'TEDx Talks',
            'uploader_id': 'TEDxTalks',
            'upload_date': '20111216',
        },
        'params': {
            'skip_download': True,
        },
    }]

    _NATIVE_FORMATS = {
        'low': {'preference': 1, 'width': 320, 'height': 180},
        'medium': {'preference': 2, 'width': 512, 'height': 288},
        'high': {'preference': 3, 'width': 854, 'height': 480},
    }

    def _extract_info(self, webpage):
        info_json = self._search_regex(r'q\("\w+.init",({.+})\)</script>',
                                       webpage, 'info json')
        return json.loads(info_json)

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url, re.VERBOSE)
        if m.group('type').startswith('embed'):
            desktop_url = m.group('proto') + 'www' + m.group('urlmain')
            return self.url_result(desktop_url, 'TED')
        name = m.group('name')
        if m.group('type_talk'):
            return self._talk_info(url, name)
        elif m.group('type_watch'):
            return self._watch_info(url, name)
        else:
            return self._playlist_videos_info(url, name)

    def _playlist_videos_info(self, url, name):
        '''Returns the videos of the playlist'''

        webpage = self._download_webpage(url, name,
                                         'Downloading playlist webpage')
        info = self._extract_info(webpage)
        playlist_info = info['playlist']

        playlist_entries = [
            self.url_result('http://www.ted.com/talks/' + talk['slug'], self.ie_key())
            for talk in info['talks']
        ]
        return self.playlist_result(
            playlist_entries,
            playlist_id=compat_str(playlist_info['id']),
            playlist_title=playlist_info['title'])

    def _talk_info(self, url, video_name):
        webpage = self._download_webpage(url, video_name)
        self.report_extraction(video_name)

        talk_info = self._extract_info(webpage)['talks'][0]

        external = talk_info.get('external')
        if external:
            service = external['service']
            self.to_screen('Found video from %s' % service)
            ext_url = None
            if service.lower() == 'youtube':
                ext_url = external.get('code')
            return {
                '_type': 'url',
                'url': ext_url or external['uri'],
            }

        formats = [{
            'url': format_url,
            'format_id': format_id,
            'format': format_id,
        } for (format_id, format_url) in talk_info['nativeDownloads'].items() if format_url is not None]
        if formats:
            for f in formats:
                finfo = self._NATIVE_FORMATS.get(f['format_id'])
                if finfo:
                    f.update(finfo)

        for format_id, resources in talk_info['resources'].items():
            if format_id == 'h264':
                for resource in resources:
                    bitrate = int_or_none(resource.get('bitrate'))
                    formats.append({
                        'url': resource['file'],
                        'format_id': '%s-%sk' % (format_id, bitrate),
                        'tbr': bitrate,
                    })
            elif format_id == 'rtmp':
                streamer = talk_info.get('streamer')
                if not streamer:
                    continue
                for resource in resources:
                    formats.append({
                        'format_id': '%s-%s' % (format_id, resource.get('name')),
                        'url': streamer,
                        'play_path': resource['file'],
                        'ext': 'flv',
                        'width': int_or_none(resource.get('width')),
                        'height': int_or_none(resource.get('height')),
                        'tbr': int_or_none(resource.get('bitrate')),
                    })
            elif format_id == 'hls':
                hls_formats = self._extract_m3u8_formats(
                    resources.get('stream'), video_name, 'mp4', m3u8_id=format_id)
                for f in hls_formats:
                    if f.get('format_id') == 'hls-meta':
                        continue
                    if not f.get('height'):
                        f['vcodec'] = 'none'
                    else:
                        f['acodec'] = 'none'
                formats.extend(hls_formats)

        audio_download = talk_info.get('audioDownload')
        if audio_download:
            formats.append({
                'url': audio_download,
                'format_id': 'audio',
                'vcodec': 'none',
                'preference': -0.5,
            })

        self._sort_formats(formats)

        video_id = compat_str(talk_info['id'])

        thumbnail = talk_info['thumb']
        if not thumbnail.startswith('http'):
            thumbnail = 'http://' + thumbnail
        return {
            'id': video_id,
            'title': talk_info['title'].strip(),
            'uploader': talk_info['speaker'],
            'thumbnail': thumbnail,
            'description': self._og_search_description(webpage),
            'subtitles': self._get_subtitles(video_id, talk_info),
            'formats': formats,
            'duration': talk_info.get('duration'),
        }

    def _get_subtitles(self, video_id, talk_info):
        languages = [lang['languageCode'] for lang in talk_info.get('languages', [])]
        if languages:
            sub_lang_list = {}
            for l in languages:
                sub_lang_list[l] = [
                    {
                        'url': 'http://www.ted.com/talks/subtitles/id/%s/lang/%s/format/%s' % (video_id, l, ext),
                        'ext': ext,
                    }
                    for ext in ['ted', 'srt']
                ]
            return sub_lang_list
        else:
            return {}

    def _watch_info(self, url, name):
        webpage = self._download_webpage(url, name)

        config_json = self._html_search_regex(
            r'"pages\.jwplayer"\s*,\s*({.+?})\s*\)\s*</script>',
            webpage, 'config')
        config = json.loads(config_json)['config']
        video_url = config['video']['url']
        thumbnail = config.get('image', {}).get('url')

        title = self._html_search_regex(
            r"(?s)<h1(?:\s+class='[^']+')?>(.+?)</h1>", webpage, 'title')
        description = self._html_search_regex(
            [
                r'(?s)<h4 class="[^"]+" id="h3--about-this-talk">.*?</h4>(.*?)</div>',
                r'(?s)<p><strong>About this talk:</strong>\s+(.*?)</p>',
            ],
            webpage, 'description', fatal=False)

        return {
            'id': name,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
        }
