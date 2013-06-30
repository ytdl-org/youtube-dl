import json
import re

from .common import InfoExtractor


class TEDIE(InfoExtractor):
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
            return [self._talk_info(url)]
        else :
            playlist_id=m.group('playlist_id')
            name=m.group('name')
            self.to_screen(u'Getting info of playlist %s: "%s"' % (playlist_id,name))
            return [self._playlist_videos_info(url,name,playlist_id)]

    def _playlist_videos_info(self,url,name,playlist_id=0):
        '''Returns the videos of the playlist'''
        video_RE=r'''
                     <li\ id="talk_(\d+)"([.\s]*?)data-id="(?P<video_id>\d+)"
                     ([.\s]*?)data-playlist_item_id="(\d+)"
                     ([.\s]*?)data-mediaslug="(?P<mediaSlug>.+?)"
                     '''
        video_name_RE=r'<p\ class="talk-title"><a href="(?P<talk_url>/talks/(.+).html)">(?P<fullname>.+?)</a></p>'
        webpage=self._download_webpage(url, playlist_id, 'Downloading playlist webpage')
        m_videos=re.finditer(video_RE,webpage,re.VERBOSE)
        m_names=re.finditer(video_name_RE,webpage)

        playlist_title = self._html_search_regex(r'div class="headline">\s*?<h1>\s*?<span>(.*?)</span>',
                                                 webpage, 'playlist title')

        playlist_entries = []
        for m_video, m_name in zip(m_videos,m_names):
            talk_url='http://www.ted.com%s' % m_name.group('talk_url')
            playlist_entries.append(self.url_result(talk_url, 'TED'))
        return self.playlist_result(playlist_entries, playlist_id = playlist_id, playlist_title = playlist_title)

    def _talk_info(self, url, video_id=0):
        """Return the video for the talk in the url"""
        m = re.match(self._VALID_URL, url,re.VERBOSE)
        video_name = m.group('name')
        webpage = self._download_webpage(url, video_id, 'Downloading \"%s\" page' % video_name)
        self.report_extraction(video_name)
        # If the url includes the language we get the title translated
        title = self._html_search_regex(r'<span id="altHeadline" >(?P<title>.*)</span>',
                                        webpage, 'title')
        json_data = self._search_regex(r'<script.*?>var talkDetails = ({.*?})</script>',
                                    webpage, 'json data')
        info = json.loads(json_data)
        desc = self._html_search_regex(r'<div class="talk-intro">.*?<p.*?>(.*?)</p>',
                                       webpage, 'description', flags = re.DOTALL)
        
        thumbnail = self._search_regex(r'</span>[\s.]*</div>[\s.]*<img src="(.*?)"',
                                       webpage, 'thumbnail')
        info = {
                'id': info['id'],
                'url': info['htmlStreams'][-1]['file'],
                'ext': 'mp4',
                'title': title,
                'thumbnail': thumbnail,
                'description': desc,
                }
        return info
