# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ENSSavoirsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?savoirs\.ens\.fr/expose\.php\?id=(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://savoirs.ens.fr/expose.php?id=2516#foo',
        'md5': 'a95f51212dd2d104fb5655bdf1d03071',
        'info_dict': {
            'id': '2516',
            'ext': 'mp4',
            'format_id': 'mp4',
            # TODO ::: Mon 23 Oct 2017 10:38:07 PM CEST
            # how to extract?
            #'formats': {
            #   'format_id': 'mp4',
            #   'tbr': 1612,
            #   'fps': 25,
            #   'acodec': 'aac',
            #   'vcodec': 'h264',
            #   'width': 360,
            #   'height': 640,
            #   'filesize_approx': '600M'
            #   },
            'title': 'Chiffrer mieux pour (dé)chiffrer plus',
            'thumbnail': r're:^https?://(?:www\.)?savoirs\.ens\.fr/uploads/images/exposes/2516\.jpg$',
            'creator': 'Anne Canteaut',
            # TODO ::: Mon 23 Oct 2017 10:38:34 PM CEST
            # hard to extract
            #'release_date': 20160413,
            #'description': "some long long text in <div id=description>"
        }
    }]

    def _real_extract(self, url):
        # TODO does this default to HTTP and not HTTPS?
        url_base = "//savoirs.ens.fr/"

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        media_url = url_base + self._html_search_regex(r'<a[^>]+href=["\'](?P<media_url>[^"\']+)["\'][^>]*>Télécharger\sla\svidéo</a>', webpage, 'media_url')
        title = self._html_search_regex(r'<span[^>]+class=["\']titrePageExpose["\'][^>]*>(?P<title>[^<]+)</span>', webpage, 'title')
        ext = media_url.split('.')[-1]
        thumbnail = "%suploads/images/exposes/%s.jpg" % (url_base, video_id)
        creator = self._html_search_regex(r'<span[^>]+class=["\']exposeConferencierNom["\'][^>]*>(?P<creator>[^<]+)</span>', webpage, 'creator', fatal=False, default="ENS Savoirs")

        return {
            'id': video_id,
            'url': media_url,
            'title': title,
            # Fails (need to extract text of <div id=description> and remove html tags)
            #'description': self._og_search_description(webpage),
            'ext': ext,
            'format_id': ext,
            'thumbnail': thumbnail,
            'creator': creator,
            #'formats': { 'format_id': ext }
            #'release_date': release_date,
        }
