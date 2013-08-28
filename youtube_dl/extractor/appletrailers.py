import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)


class AppleTrailersIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?trailers.apple.com/trailers/(?P<company>[^/]+)/(?P<movie>[^/]+)'
    _TEST = {
        u"url": u"http://trailers.apple.com/trailers/wb/manofsteel/",
        u"playlist": [
            {
                u"file": u"manofsteel-trailer4.mov",
                u"md5": u"11874af099d480cc09e103b189805d5f",
                u"info_dict": {
                    u"duration": 111,
                    u"thumbnail": u"http://trailers.apple.com/trailers/wb/manofsteel/images/thumbnail_11624.jpg",
                    u"title": u"Trailer 4",
                    u"upload_date": u"20130523",
                    u"uploader_id": u"wb",
                },
            },
            {
                u"file": u"manofsteel-trailer3.mov",
                u"md5": u"07a0a262aae5afe68120eed61137ab34",
                u"info_dict": {
                    u"duration": 182,
                    u"thumbnail": u"http://trailers.apple.com/trailers/wb/manofsteel/images/thumbnail_10793.jpg",
                    u"title": u"Trailer 3",
                    u"upload_date": u"20130417",
                    u"uploader_id": u"wb",
                },
            },
            {
                u"file": u"manofsteel-trailer.mov",
                u"md5": u"e401fde0813008e3307e54b6f384cff1",
                u"info_dict": {
                    u"duration": 148,
                    u"thumbnail": u"http://trailers.apple.com/trailers/wb/manofsteel/images/thumbnail_8703.jpg",
                    u"title": u"Trailer",
                    u"upload_date": u"20121212",
                    u"uploader_id": u"wb",
                },
            },
            {
                u"file": u"manofsteel-teaser.mov",
                u"md5": u"76b392f2ae9e7c98b22913c10a639c97",
                u"info_dict": {
                    u"duration": 93,
                    u"thumbnail": u"http://trailers.apple.com/trailers/wb/manofsteel/images/thumbnail_6899.jpg",
                    u"title": u"Teaser",
                    u"upload_date": u"20120721",
                    u"uploader_id": u"wb",
                },
            }
        ]
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        movie = mobj.group('movie')
        uploader_id = mobj.group('company')

        playlist_url = url.partition(u'?')[0] + u'/includes/playlists/web.inc'
        playlist_snippet = self._download_webpage(playlist_url, movie)
        playlist_cleaned = re.sub(r'(?s)<script>.*?</script>', u'', playlist_snippet)
        playlist_html = u'<html>' + playlist_cleaned + u'</html>'

        size_cache = {}

        doc = xml.etree.ElementTree.fromstring(playlist_html)
        playlist = []
        for li in doc.findall('./div/ul/li'):
            title = li.find('.//h3').text
            video_id = movie + '-' + re.sub(r'[^a-zA-Z0-9]', '', title).lower()
            thumbnail = li.find('.//img').attrib['src']

            date_el = li.find('.//p')
            upload_date = None
            m = re.search(r':\s?(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<year>[0-9]{2})', date_el.text)
            if m:
                upload_date = u'20' + m.group('year') + m.group('month') + m.group('day')
            runtime_el = date_el.find('./br')
            m = re.search(r':\s?(?P<minutes>[0-9]+):(?P<seconds>[0-9]{1,2})', runtime_el.tail)
            duration = None
            if m:
                duration = 60 * int(m.group('minutes')) + int(m.group('seconds'))

            formats = []
            for formats_el in li.findall('.//a'):
                if formats_el.attrib['class'] != 'OverlayPanel':
                    continue
                target = formats_el.attrib['target']

                format_code = formats_el.text
                if 'Automatic' in format_code:
                    continue

                size_q = formats_el.attrib['href']
                size_id = size_q.rpartition('#videos-')[2]
                if size_id not in size_cache:
                    size_url = url + size_q
                    sizepage_html = self._download_webpage(
                        size_url, movie,
                        note=u'Downloading size info %s' % size_id,
                        errnote=u'Error while downloading size info %s' % size_id,
                    )
                    _doc = xml.etree.ElementTree.fromstring(sizepage_html)
                    size_cache[size_id] = _doc

                sizepage_doc = size_cache[size_id]
                links = sizepage_doc.findall('.//{http://www.w3.org/1999/xhtml}ul/{http://www.w3.org/1999/xhtml}li/{http://www.w3.org/1999/xhtml}a')
                for vid_a in links:
                    href = vid_a.get('href')
                    if not href.endswith(target):
                        continue
                    detail_q = href.partition('#')[0]
                    detail_url = url + '/' + detail_q

                    m = re.match(r'includes/(?P<detail_id>[^/]+)/', detail_q)
                    detail_id = m.group('detail_id')

                    detail_html = self._download_webpage(
                        detail_url, movie,
                        note=u'Downloading detail %s %s' % (detail_id, size_id),
                        errnote=u'Error while downloading detail %s %s' % (detail_id, size_id)
                    )
                    detail_doc = xml.etree.ElementTree.fromstring(detail_html)
                    movie_link_el = detail_doc.find('.//{http://www.w3.org/1999/xhtml}a')
                    assert movie_link_el.get('class') == 'movieLink'
                    movie_link = movie_link_el.get('href').partition('?')[0].replace('_', '_h')
                    ext = determine_ext(movie_link)
                    assert ext == 'mov'

                    formats.append({
                        'format': format_code,
                        'ext': ext,
                        'url': movie_link,
                    })

            info = {
                '_type': 'video',
                'id': video_id,
                'title': title,
                'formats': formats,
                'title': title,
                'duration': duration,
                'thumbnail': thumbnail,
                'upload_date': upload_date,
                'uploader_id': uploader_id,
                'user_agent': 'QuickTime compatible (youtube-dl)',
            }
            # TODO: Remove when #980 has been merged
            info['url'] = formats[-1]['url']
            info['ext'] = formats[-1]['ext']

            playlist.append(info)

        return {
            '_type': 'playlist',
            'id': movie,
            'entries': playlist,
        }
