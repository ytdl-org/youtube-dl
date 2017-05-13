from youtube_dl.utils import parse_duration

from youtube_dl.extractor.common import InfoExtractor


class GogoAnimeIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:[\w]+\.)?gogoanime\.(?:[\w]+)/(?P<id>.*)'
    _NETRC_MACHINE = 'gogoanime'
    _TESTS = [{
        'url': 'https://www2.gogoanime.tv/naruto-shippuden-episode-1',
        'md5': 'c803e7abf0e7bb3b37391b74e0934a73',
        'info_dict': {
            'title': 'Naruto Shippuden episode 1',
            'id': 'naruto-shippuden-episode-1',
            'ext': 'mp4'
        }
    }, {
        'url': 'https://www2.gogoanime.tv/monster-strike-2',
        'md5': 'b834f7867d4e52a806f90f94a528d784',
        'info_dict': {
            'title': 'Monster Strike 2 episode 0',
            'id': 'monster-strike-2',
            'ext': 'mp4'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        web_page, urlh = self._download_webpage_handle(url, video_id)

        iframe_url = self._search_regex(
            r'src="(https://embed\.gogoanime\.[\w]+/embed\.php\?(?:.*?))"',
            web_page, 'iframe url', default=None
        )
        if iframe_url is None:
            return self.url_result(urlh.geturl(), 'Generic')

        iframe = self._download_webpage(iframe_url, video_id, 'Downloading iframe page')
        self.report_extraction(video_id)
        title = self._og_search_title(iframe) or self._search_regex(r'<title>(.*)</title>', iframe, 'title',
                                                                    default=None)
        info_dict = self._parse_html5_media_entries(url, iframe, video_id)[0]
        info_dict.update({
            'id': video_id,
            'ext': 'mp4',
            'title': title,
            'thumbnail': self._og_search_thumbnail(iframe, default=None),
        })

        return info_dict
