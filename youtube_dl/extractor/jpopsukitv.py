import re
from ..utils import unified_strdate
from .common import InfoExtractor


class JpopsukiIE(InfoExtractor):
    IE_NAME = u'jpopsuki.tv'
    _VALID_URL = r'https?://(?:www\.)?jpopsuki\.tv/video/(.*?)/(?P<id>\S+)'

    _TEST = {
        u'url': u'http://www.jpopsuki.tv/video/ayumi-hamasaki---evolution/00be659d23b0b40508169cdee4545771',
        u'md5': u'88018c0c1a9b1387940e90ec9e7e198e',
        u'file': u'00be659d23b0b40508169cdee4545771.mp4',
        u'info_dict': {
            u'id': u'00be659d23b0b40508169cdee4545771',
            u'title': u'ayumi hamasaki - evolution',
            'description': u'Release date: 2001.01.31\r 浜崎あゆみ - evolution',
            'thumbnail': u'http://www.jpopsuki.tv/cache/89722c74d2a2ebe58bcac65321c115b2.jpg',
            'uploader': u'plama_chan',
            'uploader_id': u'404',
            'upload_date': u'20121101'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = 'http://www.jpopsuki.tv' + self._html_search_regex(
            r'<source src="(.*?)" type', webpage, u'video url')

        video_title = self._html_search_regex(
            r'<meta name="og:title" content="(.*?)" />', webpage, u'video title')
        description = self._html_search_regex(
            r'<meta name="og:description" content="(.*?)" />', webpage, u'video description', flags=re.DOTALL)
        thumbnail = self._html_search_regex(
            r'<meta name="og:image" content="(.*?)" />', webpage, u'video thumbnail')
        uploader = self._html_search_regex(
            r'<li>from: <a href="/user/view/user/(.*?)/uid/', webpage, u'video uploader')
        uploader_id = self._html_search_regex(
            r'<li>from: <a href="/user/view/user/\S*?/uid/(\d*)', webpage, u'video uploader_id')
        upload_date = self._html_search_regex(
            r'<li>uploaded: (.*?)</li>', webpage, u'video upload_date')
        if upload_date is not None:
            upload_date = unified_strdate(upload_date)
        view_count = self._html_search_regex(
            r'<li>Hits: (\d*?)</li>', webpage, u'video view_count')
        comment_count = self._html_search_regex(
            r'<h2>(\d*?) comments</h2>', webpage, u'video comment_count')

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'upload_date': upload_date,
            'view_count': view_count,
            'comment_count': comment_count,
        }