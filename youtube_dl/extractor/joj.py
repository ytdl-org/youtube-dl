# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class JojIE(InfoExtractor):
    _VALID_URL = r'https?://([a-z0-9]+\.)joj\.sk/([^/]+/)*(?P<title_query>(?P<release_date>[0-9]{4}(-[0-9]{2}){2}).*)' # noqa
    _TESTS = [{
        'url': 'https://www.joj.sk/nove-byvanie/archiv/2017-05-28-nove-byvanie', # noqa
        'info_dict': {
            'id': 'a388ec4c-6019-4a4a-9312-b1bee194e932',
            'ext': 'mp4',
            'title': 'Nové Bývanie',
            'release_date': '20170528'
        }
    }, {
        'url': 'http://nasi.joj.sk/epizody/2016-09-06-stari-rodicia',
        'info_dict': {
            'id': 'f18b2c5f-9ea8-4941-a164-a814c53306ad',
            'ext': 'mp4',
            'title': 'Starí Rodičia',
            'release_date': '20160906'
        }
    }]

    media_src_url = 'http://n16.joj.sk/storage/'
    xml_source_url = 'https://media.joj.sk/services/Video.php?clip='

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title_query = mobj.group('title_query')
        release_date = mobj.group('release_date').replace('-', '')
        webpage = self._download_webpage(url, 'video_id')
        video_id = self._html_search_regex(
            r'https?://([a-z0-9]+\.)joj\.sk/embed/(?P<video_id>[a-f0-9\-]+)', webpage,
            'id', group='video_id', default=None)
        print(video_id)
        xml_playlist_url = self.xml_source_url + video_id
        xml_playlist_et = self._download_xml(xml_playlist_url, title_query)
        formats = []
        for file_el in xml_playlist_et.iter('file'):
            formats.append({'height': file_el.attrib['id'].replace('p', ''),
                            'url': self.media_src_url + file_el.attrib['path'].replace(  # noqa
                                'dat/', '', 1)})

        def get_height(d):
            return d.get('height')

        return {
            'id': video_id,
            'title': self._og_search_title(webpage).title(),
            'formats': sorted(formats, key=get_height),
            'release_date': release_date
        }
