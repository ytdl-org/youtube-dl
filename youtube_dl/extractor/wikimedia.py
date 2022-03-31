from .common import InfoExtractor
import re
import requests
import urllib.parse


class WikimediaIE(InfoExtractor):
    _NETRC_MACHINE = 'wikimediaorg'
    IE_NAME = 'wikimedia.org'
    _API_BASE_URL = 'https://commons.wikimedia.org/'
    _VALID_URL = r'https://commons.wikimedia.org/wiki/File:(?P<id>[^/]+)'

    _TEST = {
        'url': 'https://upload.wikimedia.org/wikipedia/commons/transcoded/d/d7/Die_Temperaturkurve_der_Erde_%28ZDF'
               '%2C_Terra_X%29_720p_HD_50FPS.webm/Die_Temperaturkurve_der_Erde_%28ZDF%2C_Terra_X%29_720p_HD_50FPS'
               '.webm.480p.vp9.webm',
        'ext': 'webm', 'id': 'Die_Temperaturkurve_der_Erde_(ZDF,_Terra_X)_720p_HD_50FPS.webm',
        'title': 'Die_Temperaturkurve_der_Erde_(ZDF,_Terra_X)_720p_HD_50FPS.webm',
        'license': 'This file is licensed under the Creative Commons Attribution 4.0 International license.'}

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        self.report_extraction(video_id)
        video_url = self._html_search_regex(r'<source [^>]*src="([^"]+)"', webpage,
                                            u'video URL')
        licenze = self._html_search_regex(f"(?<=td>This)(.*)(?=license.)", webpage, u'video license')
        licenze = "This " + licenze + " license."
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
        resp['ext'] = 'webm'
        resp['id'] = video_id
        resp['title'] = video_id
        resp['license'] = licenze
        return [resp]
