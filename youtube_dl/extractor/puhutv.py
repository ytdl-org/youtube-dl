# coding: utf-8
from __future__ import unicode_literals

import re
import logging
from .common import InfoExtractor


class PuhuTvIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?puhutv\.com\/(?P<display_id>[^/]+-izle)(\?[^/?]+)?'
    _URL_FORMAT = r'https?:\/\/.+\/mp4\/(?P<vid_format>[0-9]+)p\.mp4.+'

    _TEST = {
        'url': 'https://puhutv.com/isler-gucler-1-bolum-izle',
        'md5': '30f82b1b42645ef0a9de4e6eede7e714',
        'info_dict': {
            'id': 'isler-gucler-1-bolum-izle',
            'title': 'İşler Güçler 1. Sezon 1. Bölüm',
            'ext': 'mp4',
            'thumbnail': r're:^https?://.*\.(JPG|jpg)$',
            'upload_date': '20160719',
            'description': 'Ahmet, başrol oynadığı günlerin özlemini çekmekte, mazideki başarılarının göz ardı edilmesinden şikayet etmektedir. Murat, mesleğinin gereklerini yapmaya çalışırken, kendisini terketmiş olan eski sevgilisiyle beraber çalışmanın zorluklarını yaşamaktadır. Sadi, kapı gibi gümrük memurluğunu oyuncu olmak için bırakmış, para dertleri ve ailevi sorunlarla uğraşmaktadır. Figürasyon yaptığı bir tarihi diziden başka gelir kaynağı olmayan Sadi için \'Meslek Hikayeleri\'nin yayınlanması ve ücretlerini almaları çok önemlidir. \nBu sıra da programın Yapımcısı ve yapım ekibi işleri kolaylaştırmamakta güçleştirmektedir. İlginç aile üyeleri, değişik menajerleri ve olmazsa olmaz komşuları ile üçlümüzün hayatları bütün tuhaflıkları ile devam etmektedir. \'Meslek Hikayeleri\' için çektikleri ve yayınlanmayan bölümler içlerine dert olan üçlü, yayınlanabilecek kalitede bir bölüm için kolları sıvarlar. Ve ellerinden geleni de yaparlar.'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        video_data = self._download_json('https://puhutv.com/api/slug/' + str(display_id), display_id)['data']
        video_id = str(video_data['id'])
        video_title_name = video_data['title']['name']
        video_title_display_name = video_data['display_name']
        video_title = video_title_name + ' ' + video_title_display_name

        dl_data = self._download_json('https://puhutv.com/api/assets/'+video_id+'/videos', video_id)['data']

        formats = []
        mp_fmts = []
        for dl in dl_data['videos']:
            if (dl['url'].__contains__('playlist.m3u8')):
                formats.extend(self._extract_m3u8_formats(dl['url'], str(dl['id']), 'mp4'))
            elif (dl['url'].__contains__('/mp4/')):
                fmt = str(re.match(self._URL_FORMAT, dl['url']).group('vid_format'))
                mp_fmts.append({
                    'url': dl['url'],
                    'format_id': 'mp4-' + fmt,
                    'height': fmt
                })
        mp_fmts.sort(key=lambda x: int(x['height'].replace('p','')))
        formats.extend(mp_fmts)

        # extract video metadata
        thumbnail = 'https://' + video_data['content']['images']['wide']['main']
        description = video_data['description']
        upload_date = video_data['created_at'].split('T')[0].replace('-','')

        return {
            'id': display_id,
            'title': video_title,
            'formats': formats,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'description': description
        }
