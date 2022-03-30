from .common import InfoExtractor
import re
import requests
import urllib.parse


class WikimediaIE(InfoExtractor):
    _NETRC_MACHINE = 'wikimediaorg'
    IE_NAME = 'wikimedia.org'
    _API_BASE_URL = 'https://commons.wikimedia.org/'
    _VALID_URL = r'https://commons.wikimedia.org/wiki/File:(?P<id>[^/]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        self.report_extraction(video_id)
        video_url = self._html_search_regex(r'<source [^>]*src="([^"]+)"', webpage,
                                            u'video URL')
        resp = {}

        subtitle_url = f'https://commons.wikimedia.org/w/api.php?' \
                       f'action=timedtext&lang=nl&title=File%3A{urllib.parse.quote(video_id)}&trackformat=srt'
        with open(video_id + '.srt', 'w+', encoding='utf') as f:
            subtitles = requests.post(subtitle_url).text
            if 'timedtext-notfound' not in subtitles:
                f.write(subtitles)
            else:
                print("subtitles not found")
        resp['url'] = video_url
        resp['ext'] = 'webm'
        resp['id'] = video_id
        resp['title'] = video_id
        return [resp]
