# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
class AKVideoIE(InfoExtractor):
    _VALID_URL = r'https?://akvideo\.stream/video/(?P<id>\w+)'
    _TEST = {
        'url': 'https://akvideo.stream/video/0bvtm479w9iw#',
        'info_dic': {
            'id': '0bvtm479w9iw#',
            'ext': 'mp4',
            'title': 'TEST_VIDEO-C0DPdy98e4c'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = ''
        formats = []
        videoinfo = re.findall(r'download_video\(\'' + video_id + '\',\'(\w)\',\'(.*)\'\)".*<td nowrap *>(\d+)x(\d+)', webpage)
        for info in videoinfo:
            webpage = self._download_webpage('https://akvideo.stream/dl?op=download_orig&id=' + video_id + '&mode=' + info[0] + '&hash=' + info[1], video_id)

            movie_url = re.findall(r'<a class="dwnb" href="(.*?)"', webpage)
            title = str(movie_url[0]).split("/")[-1]

            formats.append({'url': movie_url[0], 'height': int(info[3]), 'width': int(info[2]) })
            time.sleep(3)

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'description': title,
            'formats': formats
        }