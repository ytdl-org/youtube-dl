# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CNNTurkIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                https?://
                    (?:www\.)?cnnturk\.com/
                    (?:
                        tv-cnn-turk/programlar/|
                        video/|
                        turkiye/|
                        dunya/|
                        ekonomi/
                    )
                    (?:[^/]+/)*
                    (?P<id>[^/?#&]+)
                '''
    _TESTS = [{
        'url': 'https://www.cnnturk.com/tv-cnn-turk/programlar/dort-bir-taraf/dort-bir-taraf-43',
        'md5': 'ea49375a769545afdb8d63d4efb46f8b',
        'info_dict': {
            'id': 'dort-bir-taraf-43',
            'ext': 'mp4',
            'title': 'Dört Bir Taraf',
            'description': r're:Altan Öymen, Nazlı Ilıcak, Enver Aysever ve .{116}$',
            'thumbnail': 'https://image.cnnturk.com/i/cnnturk/75/1200x675/542174c1cecfbe19c07cacea.jpg',
            'upload_date': '20120601',
        }
    }, {
        'url': 'https://www.cnnturk.com/tv-cnn-turk/programlar/tarafsiz-bolge/mahalle-baskisi-anayasa-tartismasi',
        'md5': 'c3999fbe0fb3366b36cb2ea56d692697',
        'info_dict': {
            'id': 'mahalle-baskisi-anayasa-tartismasi',
            'ext': 'mp4',
            'title': 'MAHALLE BASKISI - ANAYASA TARTIŞMASI',
            'description': r're:MAHALLE BASKISI ,  ANAYASA TARTIŞMASI .{96}$',
            'thumbnail': 'https://image.cnnturk.com/i/cnnturk/75/1200x675/63530cb4bf773b1104bb482d.jpg',
            'upload_date': '20120330',
        }
    }, {
        'url': 'https://www.cnnturk.com/tv-cnn-turk/programlar/edip-akbayram-enver-aysever-in-sorularini-yanitladi-aykiri-sorular-09-07-2012',
        'md5': '36814483fe64d450f35c985d5a2d2d18',
        'info_dict': {
            'id': 'edip-akbayram-enver-aysever-in-sorularini-yanitladi-aykiri-sorular-09-07-2012',
            'ext': 'mp4',
            'title': 'Edip Akbayram, Enver Aysever’in sorularını yanıtladı - Aykırı Sorular (09.07.2012)',
            'description': 'Anadolu Pop Müziğinin önde gelen isimlerinden .{94}$',
            'thumbnail': 'https://image.cnnturk.com/i/cnnturk/75/1200x675/54353b6dcecfbe1578205c80.jpg',
            'upload_date': '20120710',
        }
    }, {
        'url': 'https://www.cnnturk.com/tv-cnn-turk/programlar/aykiri-sorular/ilber-ortayli-enver-ayseverin-sorularini-yanitladi-aykiri-sorular-16-06-2014',
        'md5': '36814483fe64d450f35c985d5a2d2d18',
        'info_dict': {
            'id': 'ilber-ortayli-enver-ayseverin-sorularini-yanitladi-aykiri-sorular-16-06-2014',
            'ext': 'm3u8',
            'title': 'İlber Ortaylı Enver Aysever\'in sorularını yanıtladı: Aykırı Sorular - 16.06.2014',
            'description': 'Aykırı Sorular, Tarihçi Prof. Dr. İlber Ortaylıyı .{109}',
            'thumbnail': 'https://image.cnnturk.com/i/cnnturk/75/1200x675/54353e78cecfbe15782068ae.jpg',
            'upload_date': '20140617',
        },
        'params': {
            'skip_download': 'm3u8',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        # Video info is a JSON object inside a script tag
        video_info = self._parse_json(
            self._search_regex(
                r'({"Ancestors":.+?\);)', webpage, 'stream')[:-2],
            video_id)

        video_url = video_info['MediaFiles'][0]['Path']
        if not video_url.startswith("http"):
            video_url = 'https://cnnvod.duhnet.tv/' + video_url
        extension = 'mp4' if video_url.endswith('mp4') else 'm3u8'
        formats = [{
            'url': video_url,
            'ext': extension,
            'language': 'tr',
        }]

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'release_date': video_info['published_date'],
            'upload_date': video_info['created_date'],
            'formats': formats,
        }
