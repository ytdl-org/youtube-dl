# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class JojIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<prefix>[a-z0-9]+\.)joj\.sk/([^/]+/)*(?P<url_title>(?P<timestamp>[0-9]{4}(-[0-9]{2}){2}).*)' # noqa
    _TESTS = [ {
        'url': 'https://www.joj.sk/nove-byvanie/archiv/2017-05-28-nove-byvanie', # noqa
        'md5': '731727f2caf35a3fcaf556853f92b6e1',
        'info_dict': {
            'id': 'a388ec4c-6019-4a4a-9312-b1bee194e932',
            'ext': 'mp4',
            'title': '2017-05-28 - Nové Bývanie'
        }
    }, {
        'url': 'http://nasi.joj.sk/epizody/2016-09-06-stari-rodicia', # noqa
        'md5': '13626f2d9e237a17ea72bcaaf2738311',
        'info_dict': {
            'id': 'f18b2c5f-9ea8-4941-a164-a814c53306ad',
            'ext': 'mp4',
            'title': '2016-09-06 - Starí Rodičia'
        }
    } ]
        #       http://nasi.joj.sk/epizody/2016-09-06-stari-rodicia
        #       https://velkenoviny.joj.sk/archiv/2017-05-29-noviny-tv-joj
    def _real_extract(self, url):
        title_query = self._search_regex(self._VALID_URL, url, 'title_query',
                                         group='url_title')
        timestamp = self._search_regex(self._VALID_URL, url, 'timestamp',
                                         group='timestamp', fatal=False)
        # timestamp = '2017-05-28'
        webpage = self._download_webpage(url, title_query)
        title_simple = self._og_search_title(webpage).title()
        title = "{timestamp} - {title_simple}".format(**locals())
        video_id = self._html_search_regex(
            r'<iframe src="https://media.joj.sk/embed/(?P<id>[^\?]+)', webpage,
            'id')
        xml_url = "https://media.joj.sk/services/Video.php?clip=" + video_id
        xml_playlist = self._download_webpage(xml_url, title)
        path_to_media = self._html_search_regex(
            r'label="720p" path="(?P<path_to_media>[^"]+)"/>', xml_playlist,
            'path_to_media', group='path_to_media')
        media_url = 'http://n16.joj.sk/storage/' + path_to_media.replace('dat/', '', 1) # noqa

        return {
            'id': video_id,
            'title': title,
            'url': media_url
            # 'display_id': ''
            # 'description': self._og_search_description(webpage),
        }
