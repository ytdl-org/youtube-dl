from .common import InfoExtractor
import re
import requests
import urllib.parse
from ..utils import clean_html


class WikimediaIE(InfoExtractor):
    _NETRC_MACHINE = 'wikimediaorg'
    IE_NAME = 'wikimedia.org'
    _API_BASE_URL = 'https://commons.wikimedia.org/'
    _VALID_URL = r'https://commons.wikimedia.org/wiki/File:(?P<id>[^/]+)'

    _TEST = {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/transcoded/d/d7/Die_Temperaturkurve_der_Erde_%28ZDF'
               '%2C_Terra_X%29_720p_HD_50FPS.webm/Die_Temperaturkurve_der_Erde_%28ZDF%2C_Terra_X%29_720p_HD_50FPS'
               '.webm.480p.vp9.webm',
        'description': 'Deutsch:  Beschreibung auf der Seite: "Im Verlauf der Erdgeschichte glich das Klima einer '
                       'Achterbahnfahrt. Die „Fieberkurve“ unseres Planeten zeigt die globalen Temperaturschwankungen '
                       'bis heute – rekonstruiert anhand von historischen Klimadaten."\nZu Wikimedia Commons '
                       'hochgeladen von: PantheraLeo1359531.\nHinweise zur Weiterverwendung: '
                       'https://www.zdf.de/dokumentation/terra-x/terra-x-creative-commons-cc-100.html'
                       '.\nVereinfachender Verlauf in der Geschichte der Erde, für die Zukunft spätestens ab dem Jahr '
                       '2050 mit spekulativem Verlauf in der Prognose (ausgeprägtes Global-warming-Szenario ist '
                       'dargestellt).English:  Climate change, Temperature in history of Earth, Video of Terra X.',
        'ext': 'webm', 'id': 'Die_Temperaturkurve_der_Erde_(ZDF,_Terra_X)_720p_HD_50FPS.webm',
        'title': 'File:Die Temperaturkurve der Erde (ZDF, Terra X) 720p HD 50FPS.webm - Wikimedia Commons',
        'license': 'This file is licensed under the Creative Commons Attribution 4.0 International license.',
        'author': 'ZDF/Terra X/Gruppe 5/Luise Wagner, Jonas Sichert, Andreas Hougardy'}

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        if not video_id.endswith('.webm'):
            raise Exception("invalid video url")

        webpage = self._download_webpage(url, video_id)
        self.report_extraction(video_id)
        video_url = self._html_search_regex(r'<source [^>]*src="([^"]+)"', webpage,
                                            u'video URL')
        licenze = self._html_search_regex(f"(?<=td>This)(.*)(?=license.)", webpage, u'video license')
        licenze = "This " + licenze + " license."

        description = self._html_search_regex(f'(?<=<div class="description mw-content-ltr de" dir="ltr" lang="de">)('
                                              f'.*)(?=</div>)', webpage,
                                              u'video description')

        author = re.search(r'<td>([^\<]*?)<\/td>', str(webpage))
        author = clean_html(author.group(0))
        resp = {}

        subtitle_url = f'https://commons.wikimedia.org/w/api.php?' \
                       f'action=timedtext&lang=nl&title=File%3A{urllib.parse.quote(video_id)}&trackformat=srt'

        subtitles = requests.post(subtitle_url).text
        if 'timedtext-notfound' not in subtitles:
            with open(video_id + '.srt', 'w+', encoding='utf') as f:
                f.write(subtitles)
        else:
            print("subtitles not found")

        resp['url'] = video_url
        resp['description'] = description
        resp['ext'] = 'webm'
        resp['id'] = video_id
        resp['title'] = self._og_search_title(webpage)
        resp['license'] = licenze
        resp['author'] = author
        return [resp]
