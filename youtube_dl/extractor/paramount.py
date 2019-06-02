# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


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

    def _obtain_akamaihd_formats(self, url):
        if self._downloader.params.get('verbose', False):
            listpage = self._download_webpage(url, 'akamaihd format list')
            self.to_screen('formats page = %s' % (listpage))
        listpage = self._download_xml(url, 'akamaihd format list')
        formats = []
        for rendition in listpage.findall('./video/item/rendition'):
            fmt = {
                'width': int_or_none(rendition.get('width')),
                'height': int_or_none(rendition.get('height')),
                'url': rendition.find('./src').text
            }
            formats.append(fmt)
        return formats

    def _real_extract(self, url):
        # webpage

        webpage = self._download_webpage(url, 'webpage')

        id = self._html_search_regex(
            r'mgid:arc:content:paramount(?:network|channel)\.(?:it|es):([0-9a-f-]+)',
            webpage, 'id', fatal=False) \
	    or \
            self._html_search_regex(
            r'data-mtv-id="([0-9a-f-]*)"',
            webpage, 'id', fatal=False) \
            or \
            self._html_search_regex(
            r'"item_longId" *: *"([0-9a-f-]*)"',
            webpage, 'id')
        self.to_screen('id = %s' % (id))

        uri = self._html_search_regex(
            r'(mgid:arc:content:paramount(?:network|channel)\.(?:it|es):(?:[0-9a-f-]+))',
            webpage, 'uri', fatal=False) \
            or \
            self._html_search_regex(
            r'data-mtv-uri="([0-9a-z:\.-]*)"',
            webpage, 'uri')
        self.to_screen('uri = %s' % (uri))

        title = self._og_search_title(webpage)
        self.to_screen('title = %s' % (title))

        # list of formats

        server = 'https://mediautilssvcs-a.akamaihd.net'
        prefix = '/services/MediaGenerator/'
        arguments = 'accountOverride=esperanto.mtvi.com'
        listurl = '%s%s%s?%s' % (server, prefix, uri, arguments)
        self.to_screen('listurl = %s' % (listurl))
        formats = self._obtain_akamaihd_formats(listurl)
        if self._downloader.params.get('verbose', False):
            self.to_screen('formats = %s' % (formats))

        return {
            'id': id,
            'formats': formats,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._html_search_meta('thumbnail', webpage, fatal=False)
        }
