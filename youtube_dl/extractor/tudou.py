import re

from .common import InfoExtractor


class TudouIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?tudou\.com/(?:listplay|programs)/(?:view|(.+?))/(?:([^/]+)|([^/]+)\.html)'
    _TEST = {
        u'url': u'http://www.tudou.com/listplay/zzdE77v6Mmo/2xN2duXMxmw.html',
        u'file': u'159447792.f4v',
        u'md5': u'ad7c358a01541e926a1e413612c6b10a',
        u'info_dict': {
            u"title": u"\u5361\u9a6c\u4e54\u56fd\u8db3\u5f00\u5927\u811a\u957f\u4f20\u51b2\u540a\u96c6\u9526"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(2).replace('.html','')
        webpage = self._download_webpage(url, video_id)
        video_id = re.search('"k":(.+?),',webpage).group(1)
        title = re.search(",kw:\"(.+)\"",webpage)
        if title is None:
            title = re.search(",kw: \'(.+)\'",webpage)
        title = title.group(1)
        thumbnail_url = re.search(",pic: \'(.+?)\'",webpage)
        if thumbnail_url is None:
            thumbnail_url = re.search(",pic:\"(.+?)\"",webpage)
        thumbnail_url = thumbnail_url.group(1)
        info_url = "http://v2.tudou.com/f?id="+str(video_id)
        webpage = self._download_webpage(info_url, video_id, "Opening the info webpage")
        final_url = re.search('\>(.+?)\<\/f\>',webpage).group(1)
        ext = (final_url.split('?')[0]).split('.')[-1]
        return [{
            'id':        video_id,
            'url':       final_url,
            'ext':       ext,
            'title':     title,
            'thumbnail': thumbnail_url,
        }]
