# coding: utf-8
from __future__ import unicode_literals
from ..utils import str_to_int

from .common import InfoExtractor


class DeutschlandradioIE(InfoExtractor):
    """Information extractor for audio posts on various Deutschlandradio sites."""

    _VALID_URL = r'https?://(?:www\.)?(deutschlandradio|deutschlandradiokultur|deutschlandfunk)\.de'
    IE_NAME = 'deutschlandradio'

    _TESTS = [{
        'url': ('http://www.deutschlandfunk.de/fluechtlingskrise-es-wird-jahre-dauern-wenn-nicht.694.de.html'
                '?dram:article_id=332918'),
        'md5': '909cee0caa77d8a21a817b70af98e6ae',
        'info_dict': {
            'id': '3a945c79',
            'title': 'Trauma von Flucht und Vertreibung - Interview Ulrike Draesner, Schriftstellerin',
            "duration": 627,
            'ext': 'mp3',
            'type': 'mp3',
            'url': 'http://ondemand-mp3.dradio.de/file/dradio/2015/10/04/dlf_20151004_0715_3a945c79.mp3',
        }
    }, {
        'url': ('http://www.deutschlandradiokultur.de/bestsellerautor-marc-elsberg-wie-realistisch'
                '-sind-ihre.970.de.html?dram:article_id=330629'),
        'md5': '9b0ec52c1b1f2a091fac7489e806806a',
        'info_dict': {
            'id': '9054fc27',
            'title': 'Marc Elsberg, Bestseller-Autor von Wirtschafsthemen der digitalen Welt',
            "duration": 2050000,
            'ext': 'mp3',
            'type': 'mp3',
            'url': 'http://ondemand-mp3.dradio.de/file/dradio/2015/09/10/drk_20150910_0907_9054fc27.mp3',
        }
    }, {
        'url': ('http://www.deutschlandfunk.de/fluechtlingspolitik-ich-finde-den-alarmismus-aergerlich.'
                '694.de.html?dram:article_id=332940'),
        'md5': '4284ebe28b3552eb5ef738bec0796ece',
        'info_dict': {
            'id': '1783f974',
            'title': 'Norbert Lammert, CDU zu Neuank\u00f6mmlingen in Deutschland und deutscher Leitkultur',
            "duration": 657,
            'ext': 'mp3',
            'type': 'mp3',
            'url': 'http://ondemand-mp3.dradio.de/file/dradio/2015/10/05/dlf_20151005_0718_1783f974.mp3',
        }
    }]

    def _real_extract(self, url):
        # download webpage and extract audio link
        webpage = self._download_webpage(url, None)
        audio_tag = self._search_regex(r'<a[^>]*?data-audio-src="[^>]*?>', webpage, "play button", group=0)

        def get_attr(name, data):
            return self._html_search_regex(name + r'="([^"]+)"', data, name, group=1)

        # extract audio URL and metadata from link attributes
        audio_url = get_attr("data-audio-src", audio_tag)
        audio_ext = audio_url.split(".")[-1]
        audio_title = get_attr("data-audio-title", audio_tag)
        audio_duration = str_to_int(get_attr("data-audio-duration", audio_tag))
        audio_id = get_attr("data-audio-diraid", audio_tag)

        return {
            'id': audio_id,
            'title': audio_title,
            'url': audio_url,
            'ext': audio_ext,
            'type': audio_ext,
            'duration': audio_duration
        }


class DRadioWissenIE(InfoExtractor):
    """Information extractor for posts on DRadio Wissen."""

    _VALID_URL = r'https?://(?:www\.)?dradiowissen\.de'
    IE_NAME = 'dradiowissen'

    _TEST = {
        'url': 'http://dradiowissen.de/beitrag/indische-doktorarbeit-ueber-angela-merkel',
        'md5': '27003ff668963da7fb38dbf25018f1d0',
        'info_dict': {
            'id': 'f2c9a5fa',
            'title': 'Schaum oder Haase - Merkel aus indischer Sicht - Gespräch mit Sandra Petersmann',
            'ext': 'mp3',
            'type': 'mp3',
            'duration': 249,
            'url': ('http://ondemand-mp3.dradio.de/file/dradio/2015/10/05/'
                    'dradiowissen_merkel_aus_indischer_20151005_f2c9a5fa.mp3'),
        }
    }

    def _real_extract(self, url):
        # download webpage and extract play button
        webpage = self._download_webpage(url, None)
        audio_tag = self._search_regex(r'<button[^>]*?data-mp3="[^>]*?>', webpage, "play button", group=0)

        # extract mp3 URL and audio title from play button
        audio_url = self._html_search_regex(r'data-mp3="([^"]+)"', audio_tag, "data-mp3", group=1)
        audio_title = self._html_search_regex(r'data-title="([^"]+)"', audio_tag, "data-title", group=1)

        # extract audio id from URL
        audio_id = self._search_regex(r'^.+?_([0-9a-f]+)\.mp3$', audio_url, "id", group=1)

        # try to extract duration from title
        audio_duration = self._search_regex(
            r'^.+? \(([0-9]+:[0-9]{2})\)$',
            audio_title, "duration",
            default=None,
            fatal=False,
            group=1)
        if audio_duration is not None:
            audio_duration = audio_duration.split(":")
            audio_duration = int(audio_duration[0]) * 60 + int(audio_duration[1])

        # try to remove duration from title
        _audio_title = self._search_regex(
            r'^(.+?) \([0-9:]+\)$',
            audio_title, "title",
            default=None,
            fatal=False,
            group=1)
        if _audio_title is not None:
            audio_title = _audio_title

        return {
            'id': audio_id,
            'title': audio_title,
            'url': audio_url,
            'ext': "mp3",
            'type': "mp3",
            'duration': audio_duration
        }
