from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    url_basename,
)


class CNNIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://((edition|www)\.)?cnn\.com/video/(data/.+?|\?)/
        (?P<path>.+?/(?P<title>[^/]+?)(?:\.cnn|(?=&)))'''

    _TESTS = [{
        'url': 'http://edition.cnn.com/video/?/video/sports/2013/06/09/nadal-1-on-1.cnn',
        'file': 'sports_2013_06_09_nadal-1-on-1.cnn.mp4',
        'md5': '3e6121ea48df7e2259fe73a0628605c4',
        'info_dict': {
            'title': 'Nadal wins 8th French Open title',
            'description': 'World Sport\'s Amanda Davies chats with 2013 French Open champion Rafael Nadal.',
            'duration': 135,
            'upload_date': '20130609',
        },
    },
    {
        "url": "http://edition.cnn.com/video/?/video/us/2013/08/21/sot-student-gives-epic-speech.georgia-institute-of-technology&utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+rss%2Fcnn_topstories+%28RSS%3A+Top+Stories%29",
        "file": "us_2013_08_21_sot-student-gives-epic-speech.georgia-institute-of-technology.mp4",
        "md5": "b5cc60c60a3477d185af8f19a2a26f4e",
        "info_dict": {
            "title": "Student's epic speech stuns new freshmen",
            "description": "A Georgia Tech student welcomes the incoming freshmen with an epic speech backed by music from \"2001: A Space Odyssey.\"",
            "upload_date": "20130821",
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        path = mobj.group('path')
        page_title = mobj.group('title')
        info_url = 'http://cnn.com/video/data/3.0/%s/index.xml' % path
        info = self._download_xml(info_url, page_title)

        formats = []
        rex = re.compile(r'''(?x)
            (?P<width>[0-9]+)x(?P<height>[0-9]+)
            (?:_(?P<bitrate>[0-9]+)k)?
        ''')
        for f in info.findall('files/file'):
            video_url = 'http://ht.cdn.turner.com/cnn/big%s' % (f.text.strip())
            fdct = {
                'format_id': f.attrib['bitrate'],
                'url': video_url,
            }

            mf = rex.match(f.attrib['bitrate'])
            if mf:
                fdct['width'] = int(mf.group('width'))
                fdct['height'] = int(mf.group('height'))
                fdct['tbr'] = int_or_none(mf.group('bitrate'))
            else:
                mf = rex.search(f.text)
                if mf:
                    fdct['width'] = int(mf.group('width'))
                    fdct['height'] = int(mf.group('height'))
                    fdct['tbr'] = int_or_none(mf.group('bitrate'))
                else:
                    mi = re.match(r'ios_(audio|[0-9]+)$', f.attrib['bitrate'])
                    if mi:
                        if mi.group(1) == 'audio':
                            fdct['vcodec'] = 'none'
                            fdct['ext'] = 'm4a'
                        else:
                            fdct['tbr'] = int(mi.group(1))

            formats.append(fdct)

        self._sort_formats(formats)

        thumbnails = sorted([((int(t.attrib['height']),int(t.attrib['width'])), t.text) for t in info.findall('images/image')])
        thumbs_dict = [{'resolution': res, 'url': t_url} for (res, t_url) in thumbnails]

        metas_el = info.find('metas')
        upload_date = (
            metas_el.attrib.get('version') if metas_el is not None else None)

        duration_el = info.find('length')
        duration = parse_duration(duration_el.text)

        return {
            'id': info.attrib['id'],
            'title': info.find('headline').text,
            'formats': formats,
            'thumbnail': thumbnails[-1][1],
            'thumbnails': thumbs_dict,
            'description': info.find('description').text,
            'duration': duration,
            'upload_date': upload_date,
        }


class CNNBlogsIE(InfoExtractor):
    _VALID_URL = r'https?://[^\.]+\.blogs\.cnn\.com/.+'
    _TEST = {
        'url': 'http://reliablesources.blogs.cnn.com/2014/02/09/criminalizing-journalism/',
        'md5': '3e56f97b0b6ffb4b79f4ea0749551084',
        'info_dict': {
            'id': 'bestoftv/2014/02/09/criminalizing-journalism.cnn',
            'ext': 'mp4',
            'title': 'Criminalizing journalism?',
            'description': 'Glenn Greenwald responds to comments made this week on Capitol Hill that journalists could be criminal accessories.',
            'upload_date': '20140209',
        },
        'add_ie': ['CNN'],
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, url_basename(url))
        cnn_url = self._html_search_regex(r'data-url="(.+?)"', webpage, 'cnn url')
        return {
            '_type': 'url',
            'url': cnn_url,
            'ie_key': CNNIE.ie_key(),
        }
