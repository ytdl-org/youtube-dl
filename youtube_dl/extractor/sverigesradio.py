# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class SverigesRadioBaseIE(InfoExtractor):
    _BASE_URL = 'https://sverigesradio.se/sida/playerajax'
    _QUALITIES = ['high', 'medium', 'low']
    _CODING_FORMATS = {
        5: {'acodec': 'mp3', 'abr': 128},
        11: {'acodec': 'aac', 'abr': 192},
        12: {'acodec': 'aac', 'abr': 32},
        13: {'acodec': 'aac', 'abr': 96},
    }

    def _extract_formats(self, query, audio_id, audio_type):
        audiourls = {}
        for quality in self._QUALITIES:
            audiourl = self._download_json(
                self._BASE_URL + '/getaudiourl', audio_id,
                fatal=True,
                query=dict(query, type=audio_type, quality=quality, format='iis'))
            if audiourl is None:
                continue

            # for some reason url can be empty, skip if so
            # also skip if url has already been seen (quality parameter is ignored?)
            url = audiourl.get('audioUrl')
            if url is None or url == "" or url in audiourls:
                continue

            audioformat = {'vcodec': 'none', 'url': url}
            # add codec and bitrate if known coding format
            codingformat = audiourl.get('codingFormat')
            if codingformat:
                audioformat.update(self._CODING_FORMATS.get(codingformat, {}))

            audiourls[url] = audioformat

        return audiourls.values()

    def _extract_audio(self, audio_type, url):
        audio_id = self._match_id(url)
        query = {'id': audio_id, 'type': audio_type}

        metadata = self._download_json(self._BASE_URL + '/audiometadata', audio_id, query=query)
        item = metadata['items'][0]

        formats = self._extract_formats(query, audio_id, audio_type)
        self._sort_formats(formats)

        return {
            'id': audio_id,
            'title': item['subtitle'],
            'formats': formats,
            'series': item.get('title'),
            'duration': int_or_none(item.get('duration')),
            'thumbnail': item.get('displayimageurl'),
            'description': item.get('description'),
        }


class SverigesRadioPublicationIE(SverigesRadioBaseIE):
    _VALID_URL = r'https?://(?:www\.)?sverigesradio\.se/sida/(?:artikel|gruppsida)\.aspx\?.*artikel=(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://sverigesradio.se/sida/artikel.aspx?programid=83&artikel=7038546',
        'md5': '6a4917e1923fccb080e5a206a5afa542',
        'info_dict': {
            'id': '7038546',
            'ext': 'm4a',
            'duration': 132,
            'series': 'Nyheter (Ekot)',
            'title': 'Esa Teittinen: Sanningen har inte kommit fram',
            'description': 'md5:daf7ce66a8f0a53d5465a5984d3839df',
            'thumbnail': 're:^https://static-cdn.sr.se/sida/images/',
        },
    }, {
        'url': 'https://sverigesradio.se/sida/gruppsida.aspx?programid=3304&grupp=6247&artikel=7146887',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        return self._extract_audio('publication', url)


class SverigesRadioEpisodeIE(SverigesRadioBaseIE):
    _VALID_URL = r'https?://(?:www\.)?sverigesradio\.se/(?:sida/)?avsnitt/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://sverigesradio.se/avsnitt/1140922?programid=1300',
        'md5': '20dc4d8db24228f846be390b0c59a07c',
        'info_dict': {
            'id': '1140922',
            'ext': 'mp3',
            'duration': 3307,
            'series': 'Konflikt',
            'title': 'Metoo och valen',
            'description': 'md5:fcb5c1f667f00badcc702b196f10a27e',
            'thumbnail': 're:^https://static-cdn.sr.se/sida/images/'
        }
    }

    def _real_extract(self, url):
        return self._extract_audio('episode', url)
