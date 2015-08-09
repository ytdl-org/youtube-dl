# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_urllib_parse,
)
from ..utils import ExtractorError


def _extract_json(code):
    return re.sub(
        r'(?s)^VideoPlayer.data\("", ({.*})\);?\s*?(?://[^\n]*)*$', r'\1', code)


class PlaytvakIE(InfoExtractor):
    _VALID_URL = r'https?://.*?(playtvak|idnes|lidovky|metro)\.cz/.*\?c=(?P<id>[A-Z][0-9]{6}_[0-9]{6}_.*)'
    _TESTS = [{
        'url': 'http://www.playtvak.cz/vyzente-vosy-a-srsne-ze-zahrady-dn5-/hodinovy-manzel.aspx?c=A150730_150323_hodinovy-manzel_kuko',
        'md5': '4525ae312c324b4be2f4603cc78ceb4a',
        'info_dict': {
            'id': 'A150730_150323_hodinovy-manzel_kuko',
            'ext': 'mp4',
            'title': 'Vyžeňte vosy a sršně ze zahrady',
            'thumbnail': 'http://oidnes.cz/15/074/mobil/KUK5cea00_010hodmanel58154.jpg',
            'description': 'Málo co kazí atmosféru venkovního posezení tak jako neustálé bzučení kolem hlavy.  Vyzkoušejte náš lapač a odpuzovač vos a sršňů.',
        }
    }, {  # live video test
        'url': 'http://slowtv.playtvak.cz/planespotting-0pr-/planespotting.aspx?c=A150624_164934_planespotting_cat',
        'info_dict': {
            'id': 'A150624_164934_planespotting_cat',
            'ext': 'flv',
            'title': 're:^Přímý přenos iDNES.cz [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'thumbnail': 'http://data.idnes.cz/soubory/servisni-play-porady/89A150630_ACEK_026_VIDEOPLAYER-STREA.PNG',
            'description': 'Sledujte provoz na ranveji Letiště Václava Havla v Praze',
            'is_live': True,
        },
        'params': {
            'skip_download': True,  # requires rtmpdump
        },
    }, {  # idnes.cz
        'url': 'http://zpravy.idnes.cz/pes-zavreny-v-aute-rozbijeni-okynek-v-aute-fj5-/domaci.aspx?c=A150809_104116_domaci_pku',
        'md5': '819832ba33cd7016e58a6658577fe289',
        'info_dict': {
            'id': 'A150809_104116_domaci_pku',
            'ext': 'mp4',
            'title': 'Zavřeli jsme mraženou pizzu do auta. Upekla se',
            'thumbnail': 'http://i.idnes.cz/15/081/vidw/SHA5d1786_pizzaauto.jpg',
            'description': 'Na sociálních sítích se objevila výzva, aby lidé, kteří v horkých letních dnech uvidí v zaparkovaném autě zavřeného psa, neváhali rozbít okénko. Zastánci tohoto postoje argumentují zdravím zvířete, které v dusnu může zkolabovat. Policie doporučuje nejprve volat tísňovou linku.',
        }
    }, {  # lidovky.cz
        'url': 'http://www.lidovky.cz/dalsi-demonstrace-v-praze-o-migraci-duq-/video.aspx?c=A150808_214044_ln-video_ELE',
        'md5': 'c7209ac4ba9d234d4ad5bab7485bcee8',
        'info_dict': {
            'id': 'A150808_214044_ln-video_ELE',
            'ext': 'mp4',
            'title': 'Táhni! Demonstrace proti imigrantům budila emoce',
            'thumbnail': 'http://i.idnes.cz/15/081/vidw/PID5d1d52_vandas3.jpg',
            'description': 'Desítky lidí se sešly v Praze na protest proti imigrantům. Současně probíhala i demonstrace na jejich podporu. Na Staroměstském náměstí vystoupil i předseda dělnické strany Tomáš Vandas a kontroverzní slovenský politik Marian Kotleba. Dalšího slovenského nacionalistu Mariána Magáta odvedla policie.',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        infourl = self._html_search_regex(r'Misc.videoFLV\({ data: "([^"]+)"', webpage, 'xmlinfourl')
        parsedurl = compat_urlparse.urlparse(infourl)
        qs = compat_urlparse.parse_qs(parsedurl.query)
        if 'reklama' in qs:  # Don't ask for ads
            qs['reklama'] = ['0']
        qs['type'] = ['js']  # Ask for JS-based info file
        newquery = compat_urllib_parse.urlencode(qs, True)
        infourl = compat_urlparse.urlunparse(parsedurl[:4] + (newquery, ''))
        jsoninfo = self._download_json(infourl, video_id, transform_source=_extract_json)

        item = None
        for i in jsoninfo['items']:
            if i['type'] == 'video' or i['type'] == 'stream':
                item = i
                break
        if item is None:
            raise ExtractorError('No suitable stream found')
        title = item['title']
        thumbnail = item['image']
        is_live = item['type'] == 'stream'
        if is_live:
            title = self._live_title(title)

        formats = []
        for fmt in item['video']:
            format_entry = {'url': fmt['file'],
                            'format_id': ("%s_%s" % (fmt['format'], fmt['quality'])),
                            }
            if fmt['quality'] == 'middle':
                format_entry['quality'] = -2
            elif fmt['quality'] == 'low':
                format_entry['quality'] = -3

            if fmt['format'] == 'mp4':
                format_entry['ext'] = 'mp4'
            elif fmt['format'] == 'webm':
                format_entry['ext'] = 'webm'
            elif fmt['format'] == 'apple':
                format_entry['ext'] = 'mp4'
                format_entry['protocol'] = 'm3u8'
                # Some streams have mp3 audio which does not play
                # well with ffmpeg filter aac_adtstoasc
                format_entry['preference'] = -1
            elif fmt['format'] == 'rtmp':
                format_entry['ext'] = 'flv'
            else:  # Other formats not supported yet
                continue

            formats.append(format_entry)

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': self._og_search_description(webpage),
            'is_live': is_live,
            'formats': formats,
        }
