# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import get_element_by_class, determine_ext, clean_html, KNOWN_EXTENSIONS
import re


class WikimediaIE(InfoExtractor):
    _NETRC_MACHINE = 'wikimediaorg'
    IE_NAME = 'wikimedia.org'
    _API_BASE_URL = 'https://commons.wikimedia.org/'
    _VALID_URL = r'https://commons.wikimedia.org/wiki/File:(?P<id>[^/]+)'

    _TEST = {
        'url': 'https://commons.wikimedia.org/wiki/File:Die_Temperaturkurve_der_Erde_(ZDF,_Terra_X)_720p_HD_50FPS.webm',
        'info_dict': {
            'description': 'md5:D6F4C7BF1C0DB1EAE80371B1F93EA85E',
            'ext': 'webm',
            'id': 'Die_Temperaturkurve_der_Erde_(ZDF,_Terra_X)_720p_HD_50FPS',
            'title': 'Die Temperaturkurve der Erde (ZDF, Terra X) 720p HD 50FPS.webm - Wikimedia Commons',
            'license': 'This file is licensed under the Creative Commons Attribution 4.0 International license.',
            'author': 'ZDF/Terra X/Gruppe 5/Luise Wagner, Jonas Sichert, Andreas Hougardy',
            'subtitles': {'de': [
                {'ext': 'srt',
                 'url': 'https://commons.wikimedia.org/w/api.php?action=timedtext&amp&title=File%3ADie_Temperaturkurve_der_Erde_%28ZDF%2C_Terra_X%29_720p_HD_50FPS.webm&amp&lang=de&amp&trackformat=srt'}],
                'en-gb': [
                    {'ext': 'srt',
                     'url': 'https://commons.wikimedia.org/w/api.php?action=timedtext&amp&title=File%3ADie_Temperaturkurve_der_Erde_%28ZDF%2C_Terra_X%29_720p_HD_50FPS.webm&amp&lang=en-gb&amp&trackformat=srt'}],
                'nl': [
                    {'ext': 'srt',
                     'url': 'https://commons.wikimedia.org/w/api.php?action=timedtext&amp&title=File%3ADie_Temperaturkurve_der_Erde_%28ZDF%2C_Terra_X%29_720p_HD_50FPS.webm&amp&lang=nl&amp&trackformat=srt'}
                ]}
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        ext = determine_ext(url)
        if not ext.lower() in KNOWN_EXTENSIONS:
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
        info['ext'] = ext
        info['id'] = video_id.replace('.' + ext, "")
        info['title'] = self._og_search_title(webpage).replace("File:", "")
        info['license'] = licenze
        info['author'] = author

        subtitles = {}
        for sub in re.findall(r'\bsrc=\"\/w\/api\s*(.*?)\s*srt\b', str(webpage)):
            sub = 'https://commons.wikimedia.org/w/api' + sub + 'srt'
            lang = sub[sub.find('lang=') + 5:]
            lang = lang[:lang.find('&')]
            sub = sub.replace(';', '&')
            info['subtitles'][lang] = [{"ext": "srt", "url": sub}]

        info['subtitles'] = subtitles
        return info
