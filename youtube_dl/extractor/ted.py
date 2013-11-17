import json
import re

from .subtitles import SubtitlesInfoExtractor

from ..utils import (
    compat_str,
    RegexNotFoundError,
)

class TEDIE(SubtitlesInfoExtractor):
    _VALID_URL=r'''http://www\.ted\.com/
                   (
                        ((?P<type_playlist>playlists)/(?P<playlist_id>\d+)) # We have a playlist
                        |
                        ((?P<type_talk>talks)) # We have a simple talk
                   )
                   (/lang/(.*?))? # The url may contain the language
                   /(?P<name>\w+) # Here goes the name and then ".html"
                   '''
    _TEST = {
        u'url': u'http://www.ted.com/talks/dan_dennett_on_our_consciousness.html',
        u'file': u'102.mp4',
        u'md5': u'2d76ee1576672e0bd8f187513267adf6',
        u'info_dict': {
            u"description": u"md5:c6fa72e6eedbd938c9caf6b2702f5922", 
            u"title": u"Dan Dennett: The illusion of consciousness"
        }
    }

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def _real_extract(self, url):
        m=re.match(self._VALID_URL, url, re.VERBOSE)
        if m.group('type_talk'):
            return self._talk_info(url)
        else :
            playlist_id=m.group('playlist_id')
            name=m.group('name')
            self.to_screen(u'Getting info of playlist %s: "%s"' % (playlist_id,name))
            return [self._playlist_videos_info(url,name,playlist_id)]


    def _playlist_videos_info(self, url, name, playlist_id):
        '''Returns the videos of the playlist'''

        webpage = self._download_webpage(
            url, playlist_id, u'Downloading playlist webpage')
        matches = re.finditer(
            r'<p\s+class="talk-title[^"]*"><a\s+href="(?P<talk_url>/talks/[^"]+\.html)">[^<]*</a></p>',
            webpage)

        playlist_title = self._html_search_regex(r'div class="headline">\s*?<h1>\s*?<span>(.*?)</span>',
                                                 webpage, 'playlist title')

        playlist_entries = [
            self.url_result(u'http://www.ted.com' + m.group('talk_url'), 'TED')
            for m in matches
        ]
        return self.playlist_result(
            playlist_entries, playlist_id=playlist_id, playlist_title=playlist_title)

    def _talk_info(self, url, video_id=0):
        """Return the video for the talk in the url"""
        m = re.match(self._VALID_URL, url,re.VERBOSE)
        video_name = m.group('name')
        webpage = self._download_webpage(url, video_id, 'Downloading \"%s\" page' % video_name)
        self.report_extraction(video_name)
        # If the url includes the language we get the title translated
        title = self._html_search_regex(r'<span .*?id="altHeadline".+?>(?P<title>.*)</span>',
                                        webpage, 'title')
        json_data = self._search_regex(r'<script.*?>var talkDetails = ({.*?})</script>',
                                    webpage, 'json data')
        info = json.loads(json_data)
        desc = self._html_search_regex(r'<div class="talk-intro">.*?<p.*?>(.*?)</p>',
                                       webpage, 'description', flags = re.DOTALL)
        
        thumbnail = self._search_regex(r'</span>[\s.]*</div>[\s.]*<img src="(.*?)"',
                                       webpage, 'thumbnail')
        formats = [{
            'ext': 'mp4',
            'url': stream['file'],
            'format': stream['id']
        } for stream in info['htmlStreams']]

        video_id = info['id']

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, webpage)
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, webpage)
            return

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': desc,
            'subtitles': video_subtitles,
            'formats': formats,
        }

    def _get_available_subtitles(self, video_id, webpage):
        try:
            options = self._search_regex(r'(?:<select name="subtitles_language_select" id="subtitles_language_select">)(.*?)(?:</select>)', webpage, 'subtitles_language_select', flags=re.DOTALL)
            languages = re.findall(r'(?:<option value=")(\S+)"', options)
            if languages:
                sub_lang_list = {}
                for l in languages:
                    url = 'http://www.ted.com/talks/subtitles/id/%s/lang/%s/format/srt' % (video_id, l)
                    sub_lang_list[l] = url
                return sub_lang_list
        except RegexNotFoundError as err:
            self._downloader.report_warning(u'video doesn\'t have subtitles')
        return {}
