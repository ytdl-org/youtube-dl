# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ParamountIE(InfoExtractor):
    IE_NAME = 'paramount'
    IE_DESC = 'Paramount Network'
    _VALID_URL = r'http(s)?://(www\.)?paramountnetwork\.(it|es)/.*/[0-9a-z]{6}($|/)'

    _TEST = {
        'url': 'http://www.paramountnetwork.it/playlist/speciali-paramount-channel/o3gr12/speciale-stephen-king/x0xj9k',
        'md5': '4079336559ea61e24eb08b1b1adf2523',
        'info_dict': {
            'id': 'dbf6d5d5-1a95-41ac-b17b-b5caca227b25',
            'ext': 'mp4',
            'title': 'SPECIALE STEPHEN KING - Speciali video, Paramount Network',
            'description': 'Tutti gli speciali di Paramount Network curiosità, approfondimenti e aggiornamenti su film, serie tv e personaggi del cinema.'
        }
    }

    def _real_extract(self, url):
        # webpage

        webpage = self._download_webpage(url, 'webpage')
        # self.to_screen('webpage = %s' % (webpage))

        id = self._html_search_regex(
            r'mgid:arc:content:web.paramount(?:network|channel|plus)\.(?:it|es|com):([0-9a-f-]+)',
            webpage, 'id')
        self.to_screen('id = %s' % (id))

        episode = self._html_search_regex(
            r'mgid:arc:episode:paramount.intl:([0-9a-f-]+)',
            webpage, 'episode', fatal=False) \
            or \
            self._html_search_regex(
            r'"contentId" *: *"([0-9a-f-]*)"',
            webpage, 'episode')
        self.to_screen('episode = %s' % (episode))

        title = self._og_search_title(webpage)
        self.to_screen('title = %s' % (title))

        # episode page

        server = 'https://media.mtvnservices.com'
        prefix = '/pmt/e1/access/index.html'
        argument1 = 'uri=mgid:arc:episode:paramount.intl:%s' % (episode)
        argument2 = 'configtype=edge'
        epurl = '%s%s?%s&%s' % (server, prefix, argument1, argument2)
        self.to_screen('epurl = %s' % (epurl))
        eppage = self._download_webpage(epurl, 'episode url page',
                                        headers={'Referer': url})
        self.to_screen('format list page = %s' % (eppage))

        uri = self._html_search_regex(
            r'(mgid:arc:video:paramount.intl:(?:[0-9a-f-]+))',
            eppage, 'uri')
        self.to_screen('uri = %s' % (uri))

        ep = self._html_search_regex(
            r'&ep=([0-9a-f-]+)"',
            eppage, 'ep')
        self.to_screen('ep = %s' % (ep))

        # list of formats

        server = 'https://media-utils.mtvnservices.com'
        prefix = '/services/MediaGenerator/'
        arg1 = 'arcStage=live&accountOverride=intl.mtvi.com&ep=%s' % (ep)
        arg2 = '&acceptMethods=hls&format=json&https=true&isEpisode=true'
        listurl = '%s%s%s?%s%s' % (server, prefix, uri, arg1, arg2)
        self.to_screen('listurl = %s' % (listurl))

        listpage = self._download_json(listurl, 'url list page')
        self.to_screen('listpage = %s' % (listpage))
        src = listpage['package']['video']['item'][0]['rendition'][0]['src']
        self.to_screen('src = %s' % (src))

        return {
            'id': id,
            'formats': self._extract_m3u8_formats(src, id),
            'title': title,
            'description': self._og_search_description(webpage),
        }
