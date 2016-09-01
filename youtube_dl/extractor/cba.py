# coding: utf-8
from __future__ import unicode_literals

import datetime
import os

from .common import InfoExtractor
from ..utils import (
    clean_html,
    ExtractorError,
    strip_bom_utf8,
    RegexNotFoundError,
    UnavailableVideoError,
    update_url_query,
)

class CBAIE(InfoExtractor):
    IE_NAME = 'cba'
    IE_DESC = 'cultural broadcasting archive'
    _VALID_URL = r'https?://(?:www\.)?cba\.fro\.at/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://cba.fro.at/320619',
        'md5': 'e40379688fcc5e95d6d8a482bb665b02',
        'info_dict': {
            'id': '320619',
            'ext': 'mp3',
            'title': 'Radio Netwatcher Classics vom 15.7.2016 – Peter Pilz, Sicherheitssprecher Grüne über die nationale Entwicklung zum Überwachungsstaat',
            'url': 'https://cba.fro.at/wp-content/uploads/radio_netwatcher/netwatcher-20160715.mp3',
            'description': 'Peter Pilz von den Grünen zu Gast in Radio Netwatcher 2008\nRadio Netwatcher Classics 2016 – Das Sommerprogramm in deinem Freien Radio\nPeter Pilz über nationale Entwicklung zum Polizeistaat zu Gast in Radio Netwatcher 2008\nqtalk v. 29.1.2008 Thema:“Österreich auf dem Weg in den Polizeistaat?“\nDas neue SicherheitsPolizeiGesetz aus Sicht von NR Peter Pilz (Die Grünen)\nIm Biedermeier setzte Metternich durch die Karlsbader Beschlüsse von 1819 eine strenge Zensur und eine starke Einschränkung jeglicher politischer Betätigung durch. In einem mehr als fragwürdigen Eilverfahren wurden die Beschlüsse vom Bundestag in Frankfurt einstimmig bestätigt, obwohl sie tief in die Rechte der Einzelstaaten des Deutschen Bundes eingriffen. Erst mit der bürgerlichen Märzrevolution von 1848 gelang es, sich aus einem System von Verfolgung und Zensur durch die Polizei zu befreien.\nDie jüngsten Ereignisse in Österreich und der EU zeigen beängstigende Parallelen. In einer überfallartigen Übernacht-Aktion beschließt der Nationalrat gegen Mitternacht des 6. Dezember 2007 die Novelle zum Sicherheitspolizeigesetz – ohne die in Österreich üblichen Begutachtungen von neuen Gesetzen und ohne Vorlage beim Innenausschuss des Parlamentes.\nAusgehehelt wurde mit dieser Novelle auch das Prinzip der österreichischen Gewaltenteilung: Erstmalig ist es der Polizei ohne richterlichen Befehl gestattet den aktuellen Standort unserer Mobiltelefonen abzufragen, einen IMSI-Catcher einzusetzen (und damit unsere Handytelefonate mitzuhören) und von den Netzbetreibern Auskunft über dynamische IP-Adressen zu erzwingen (und damit unsere private Internetnutzung zu erfragen).\nDie massive und dabei noch stetige Ausweitung der Polizeibefugnisse durch das Sicherheitspolizeigesetz öffnet die Tür in den Überwachungsstaat. Immer umfassender wollen uns Polizei und Nachrichtendienste kontrollieren: durch Maßnahmen wie Lauschangriff, Rasterfahndung, Bundestrojaner, Bildungsevidenz, Videoüberwachung, Fingerabdrücke, Genmusterabdrücke, Vorratsdatenspeicherung und IMSI-Catcher.\nWir sind der Überzeugung, dass nicht alles zulässig sein darf, was technisch möglich ist. Verfassung, Justiz und Polizei haben eine gemeinsame Aufgabe: Uns und unsere Freiheit zu schützen. Immer öfter wächst aber aus vermeintlichem Schutz eine Bedrohung heran. Und immer öfter geht eine schrankenlose Überwachung auf Kosten unserer Freiheit und Demokratie. Denn Menschen, die sich überwacht fühlen, sind nicht mehr bereit eine eigene Meinung zu äußern.\nPeter Pilz von den Grünen hat eine Petition – Gegen die Ausweitung der polizeilichen Überwachung – initiert: „Wir erwarten vom österreichischen Nationalrat Sorgfalt und Verantwortungsbewusstsein im Umgang mit den Grundrechten der Menschen und der Verfassung der Republik.“\nPetition der Grünen: http://www.ueberwachungsstaat.at/\nWenn einseitige Sicherheitspolitik die Freiheit gefährdet, ist es Zeit die Freiheit vor der Sicherheitspolitik zu schützen.\nhttp://www.quintessenz.at/d/000100004175\nMit der Veranstaltungsreihe q/talk lädt die q/uintessenz zu Fachvorträgen über die Themen Bürgerrechte und neue Technologien monatlich ins MQ Wien. http://www.quintessenz.at/\nqTalk by q/uintessenz\nBeteiligte:\nRadio Netwatcher – Redaktionsteam (Verfasser/in oder Urheber/in)\nQuelle: https://cba.fro.at/72100\n \nPlaylist / Bonustrack:  Rockit Gaming – POKEMON GO RAP SONG'
        }
    }
    _FORMATS = {
        'audio/ogg': {'id': '1', 'ext': 'ogg', 'preference': 100},
        'audio/mpeg': {'id': '2', 'ext': 'mp3', 'preference': 50}
    }
    _API_KEY = None

    def __init__(self, *args, **kwargs):
        try:
            self._API_KEY = os.environ["CBA_API_KEY"]
        except KeyError:
            pass

    def _add_optional_parameter(self, formats, name, data, key, convert=None):
        try:
            param = data[key]
            if convert:
                param = convert(param)
            formats[name] = param
        except KeyError:
            pass

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_posts_url = "https://cba.fro.at/wp-json/wp/v2/posts/%s" % video_id
        api_media_url = "https://cba.fro.at/wp-json/wp/v2/media?media_type=audio&parent=%s" % video_id

        title = 'unknown'
        description = ''
        formats = []

        posts_result = self._download_json(api_posts_url, video_id, 'query posts api-endpoint',
                                           'unable to query posts api-endpoint', transform_source=strip_bom_utf8)
        try:
            title = clean_html(posts_result['title']['rendered'])
            description = clean_html(posts_result['content']['rendered'])
        except KeyError:
            pass

        api_key_str = " (without API_KEY)"
        if self._API_KEY:
            api_key_str =  " (using API_KEY '%s')" % self._API_KEY
            api_media_url = update_url_query(api_media_url, {'c': self._API_KEY})

        media_result = self._download_json(api_media_url, video_id, 'query media api-endpoint%s' % api_key_str,
                                         'unable to qeury media api-endpoint%s' % api_key_str, transform_source=strip_bom_utf8)
        for media in media_result:
            try:
                url = media['source_url']
                if url == "":
                    continue

                ft = media['mime_type']
                f = { 'url': url, 'format': ft, 'format_id': self._FORMATS[ft]['id'], 'preference': self._FORMATS[ft]['preference'] }
                self._add_optional_parameter(f, 'filesize', media['media_details'], 'filesize')
                self._add_optional_parameter(f, 'abr', media['media_details'], 'bitrate', lambda x: x/1000)
                self._add_optional_parameter(f, 'asr', media['media_details'], 'sample_rate')

                formats.append(f)
            except KeyError:
                pass

        if len(formats) == 0:
            if self._API_KEY:
                raise ExtractorError('unable to fetch CBA entry')
            else:
                raise UnavailableVideoError('you may need an API key to download copyright protected files')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
