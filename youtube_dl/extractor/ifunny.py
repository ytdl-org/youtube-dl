from .common import InfoExtractor

class IFunnyIE(InfoExtractor):
    _VALID_URL = r'(?:https?:\/\/)?(?:www\.)?ifunny\.co\/fun\/(?P<id>\w+)'

    _TEST = {
        u'url': u'https://ifunny.co/fun/pQ0qJYrT5',
        u'file': u'Found on iFunny-pQ0qJYrT5.mp4',
        u'md5': u'1e6486c492bbefe5fcc2291c9d891000',
        u'info_dict': {
            u"id": u"pQ0qJYrT5",
            u"ext": u"mp4",
            u"title": u"Found on IFunny"
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage_url = 'https://ifunny.co/fun/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        # Log that we are starting to parse the page
        self.report_extraction(video_id)

        video_url = self._html_search_regex(r'<meta property="og:video" content="(.+?)"', webpage,
                                            u'video URL')
        return [{
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
        }]