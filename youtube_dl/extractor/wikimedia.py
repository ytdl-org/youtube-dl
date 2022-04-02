from .common import InfoExtractor
from ..utils import get_element_by_class, compat_urlparse, clean_html
import re


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
        'title': 'Die Temperaturkurve der Erde (ZDF, Terra X) 720p HD 50FPS.webm - Wikimedia Commons',
        'license': 'This file is licensed under the Creative Commons Attribution 4.0 International license.',
        'author': 'ZDF/Terra X/Gruppe 5/Luise Wagner, Jonas Sichert, Andreas Hougardy', 'subtitles': {'nl': [
            {'ext': 'srt',
             'url': 'https://commons.wikimedia.org/w/api.php?action=timedtext&lang=nl&title=File'
                    '%3ADie_Temperaturkurve_der_Erde_%28ZDF%2C_Terra_X%29_720p_HD_50FPS.webm&trackformat=srt'}]}}

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if not video_id.endswith('.webm'):
            raise Exception("invalid video url")

        webpage = self._download_webpage(url, video_id)
        self.report_extraction(video_id)
        video_url = self._html_search_regex(r'<source [^>]*src="([^"]+)"', webpage,
                                            u'video URL')
        licenze = self._html_search_regex(r'\bThis\s*(.*?)\s*license\b', webpage, u'video license')
        licenze = "This " + licenze + " license."

        description = get_element_by_class('description', webpage)
        author = self._html_search_regex(r'<td>([^\<]*?)<\/td>', str(webpage), u"video author")
        info = {}

        info['url'] = video_url
        info['description'] = clean_html(description)
        info['ext'] = 'webm'
        info['id'] = video_id[:-5]
        info['title'] = self._og_search_title(webpage).replace("File:", "")
        info['license'] = licenze
        info['author'] = author

        subtitles = re.findall(r'\bsrc=\"\/w\/api\s*(.*?)\s*srt\b', str(webpage))
        info['subtitles'] = {}
        for sub in subtitles:
            sub = 'https://commons.wikimedia.org/w/api' + sub + 'srt'
            lang = sub[sub.find('lang=') + 5:]
            lang = lang[:lang.find('&')]
            info['subtitles'][lang] = [{"ext": "srt", "url": sub}]
        return info
