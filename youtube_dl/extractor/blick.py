# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class BlickIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?blick\.ch/.*-id(?P<id>\d+).*\.html'

    _TESTS = [{
        'url': 'http://www.blick.ch/sport/uli-forte-vor-dem-abstiegs-showdown-ich-gehe-davon-aus-dass-der-fussball-gott-fcz-fan-ist-id5070813.html',
        'info_dict': {
            'id': '5070813',
            'ext': 'mp4',
            'title': 'uli-forte-vor-dem-abstiegs-showdown-ich-gehe-davon-aus-dass-der-fussball-gott-fcz-fan-ist',
            'thumbnail': 'http://blick.simplex.tv/content/51/52/70062/simvid_1.jpg',
            'description': 'Am Mittwochabend entscheidet sich, ob der FCZ oder der FC Lugano aus der Super League absteigt. Uli Forte schwört dabei auf den Fussball-Gott und zündet in der Kirche eine Kerze an.'
        }
    }, {
        'url': 'http://www.blick.ch/sport/tennis/nominiert-fuer-musik-preis-in-schweden-so-toll-singt-guenthardts-tochter-alessandra-id5066863.html',
        'info_dict': {
            'id': '5066863',
            'ext': 'mp4',
            'title': 'nominiert-fuer-musik-preis-in-schweden-so-toll-singt-guenthardts-tochter-alessandra',
            'thumbnail': 'http://f.blick.ch/img/incoming/crop5066860/5146024130-csquare-w300-h300/Bildschirmfoto-2016-05-23-um-14.jpg',
            'description': 'Da ist Papa Heinz mächtig stolz. Seine Tochter Alessandra Günthardt ist für einen schwedischen Musik-Preis unter den drei Nominierten. Die Abstimmung läuft noch bis 7. Juni.'
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        found_videos_og = re.findall(r'<meta.*?property="og:video".*?content="(.*?)"', webpage)
        found_videos_ogs = re.findall(r'<meta.*?property="og:video".*?content="(.*?)"', webpage)
        found_videos_meta = re.findall(r'<meta.*?itemprop="contentURL".*?content="(.*?)"', webpage)
        found_videos = found_videos_og + found_videos_ogs + found_videos_meta
        video_url = ''
        for video in found_videos:
            if re.match(r'.*detect\.mp4', video):
                ind = video.rfind('/')
                video_url = video[:ind + 1]
                video_url += 'index.m3u8'
                break
            elif re.match(r'.*\.m3u8', video):
                video_url = video
                break

        if not video_url:
            return []

        video_title = str(url)
        b_ind = video_title.rfind('/') + 1
        e_ind = video_title.rfind('-id')
        video_title = video_title[b_ind:e_ind]

        video_description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        entry_info_dict = {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'thumbnail': thumbnail,
            'duration': None,
        }
        entry_info_dict['formats'] = self._extract_m3u8_formats(
            video_url,
            video_id,
            ext='mp4',
            entry_protocol='m3u8_native')

        if entry_info_dict.get('formats'):
            self._sort_formats(entry_info_dict['formats'])

            # Remove entries containing a url to an index.m3u8 file
            cleaned_formats = [x for x in entry_info_dict['formats'] if x.get('format_id') != 'meta']
            entry_info_dict['formats'] = cleaned_formats

            duration_found = False
            duration = None
            attr = ''
            for elem in entry_info_dict.get('formats'):
                if not duration_found:
                    duration = self.calculateDuration(elem['url'], video_id)
                    duration_found = True if duration else False
                tbr = elem.get('tbr')
                try:
                    attr = ''
                    if tbr < 1000:
                        attr = 'lq'
                    elif tbr >= 1000 and tbr < 2000:
                        attr = 'sq'
                    elif tbr >= 2000:
                        attr = 'hq'
                except TypeError:
                    attr = 'un'
                elem['format_id'] = attr + '-' + str(tbr)
        entry_info_dict['duration'] = duration
        return entry_info_dict

    def calculateDuration(self, m3u8_url, video_id):
        content = self._download_webpage_handle(
            m3u8_url,
            video_id,
            note='Downloading m3u8 information',
            errnote='Failed to download m3u8 information',
            fatal=False
        )
        if content is False:
            return None
        m3u8_doc, rlh = content
        duration = 0.0
        try:
            for line in m3u8_doc.splitlines():
                if line.startswith('#EXTINF:'):
                    dur = line[8:].strip()[:-1]
                    duration += float(dur)
        except ValueError:
            return None
        return duration
