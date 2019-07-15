# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    month_by_name,
    int_or_none,
    str_or_none,
)


class ArteRadioIE(InfoExtractor):
    """ArteRadio sound extractor."""
    IE_NAME = 'arteradio'
    _VALID_URL = r'https?://(?:www\.)?arteradio\.com/son/(?P<id>\d+)/(.*)'
    _CDN_URL = 'https://download.www.arte.tv/permanent/arteradio/sites/default/files/sons/'

    _TESTS = [{
        'url': 'https://www.arteradio.com/son/616458/la_bas_si_j_y_suis_plus',
        'md5': 'ae9219bbcfbb258ab5d5ba877708e2a9',
        'info_dict': {
            'id': '616458',
            'ext': 'mp3',
            'title': 'Là-bas si j\'y suis plus | ARTE Radio',
            'upload_date': '20140911',
            'description': 'md5:863c01af898a02681a2f543d32031566',
            'vcodec': 'none',
            'duration': 917,
        },
    }, {
        'url': 'https://www.arteradio.com/son/61661758/bande_annonce_beatmakers_saison_2',
        'md5': 'a4678484b374e35faf47a555860a0a4f',
        'info_dict': {
            'id': '61661758',
            'ext': 'mp3',
            'title': 'Bande-annonce Beatmakers, saison 2 | ARTE Radio',
            'upload_date': '20190627',
            'description': 'md5:d52a0fd2fcc88e2d4b1cd0f2a5092fd1',
            'vcodec': 'none',
            'duration': 56,
            'thumbnail': 'https://www.arteradio.com/sites/default/files/beatmakers_s2_1.jpg'
        },
    }]

    def _extract_date(self, webpage):
        # Fetching date
        upload_date_str = self._html_search_regex(
            r'<h5[^>]*>Mise en ligne.+<\/h5>\s+<p>(.+)<\/p>',
            webpage, 'upload_date_str', fatal=False, default=None)
        if not upload_date_str:
            return None
        try:
            day, month, year = upload_date_str.split(' ')
            day = '{:02d}'.format(int_or_none(day))
            month = '{:02d}'.format(month_by_name(month, lang='fr'))
        except (ValueError, TypeError):
            return None
        return ''.join((year, month, day))

    def _extract_data_from_button(self, button):
        meta_data = dict(re.findall(r'data-([-\w]+?)=\"(.+?)\"', button))
        # If no sound-href is found we cannot extract the link
        try:
            url = self._CDN_URL + meta_data['sound-href']
        except KeyError:
            raise ExtractorError('No audio found')
        return {
            'id': meta_data.get('sound-id'),
            'duration': int_or_none(meta_data.get('duration-seconds')),
            'url': url,
            'href': meta_data.get('href'),
            'position': meta_data.get('position-serie'),
            'thumbnail': meta_data.get('image-url'),
            'vcodec': 'none',
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        button = self._html_search_regex(
            r'<button([^>]+data-sound-id=\"{}\"[^>]*)>'.format(video_id),
            webpage, 'button')
        audio_data = self._extract_data_from_button(button)
        result = {
            'id': audio_data['id'] or video_id,
            'duration': audio_data['duration'],
            'url': audio_data['url'],
            'thumbnail': audio_data['thumbnail'],
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'upload_date': str_or_none(self._extract_date(webpage)),
        }
        result.update(audio_data)
        return result


class ArteRadioSerieIE(ArteRadioIE):
    """ArteRadio serie extractor."""
    IE_NAME = 'arteradio.com:playlist'
    _VALID_URL = r'https?://(?:www\.)?arteradio\.com/serie/(?P<id>.+)'

    _TESTS = [{
        'url': 'https://www.arteradio.com/serie/crackopolis',
        'md5': '',
        'info_dict': {
            'id': 'crackopolis',
            'title': 'CRACKOPOLIS | ARTE Radio',
            'description': 'md5:1b4665891ef07bef17c98d692435d177',
        },
        'playlist_count': 16
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        button_entries = re.findall(
            r'<button([^>]+data-serie-url=\"/serie/{}\"[^>]*)>'.format(playlist_id),
            webpage)
        entries = [self._extract_data_from_button(button) for button in button_entries]
        # The title for an item is not in the item meta data
        # We generate the title from the item url
        for index, entry in enumerate(entries):
            position = entry.get('position') or index
            try:
                title = entry.get('href', '').split('/')[3]
            except IndexError:
                title = playlist_id
            entry['title'] = position + '_' + title

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        return self.playlist_result(entries, playlist_id, title, description)
