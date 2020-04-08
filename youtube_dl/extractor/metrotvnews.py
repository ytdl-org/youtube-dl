from __future__ import unicode_literals

from .common import InfoExtractor




class MetrotvnewsIE(InfoExtractor):
    _VALID_URL = r'https:\/\/www.metrotvnews\.com\/play\/(?P<id>\S+)-\S+'


    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id
        )

        title = self._html_search_regex(r'<title>(.+) - www.metrotvnews.com<\/title>', webpage, 'title')
        '''
        download_url = self._html_search_regex(

            r'(https:\/\/celebsroulette\.com\/get_file\/1\/\S+\/[0-9]+\/[0-9]+\/[0-9]+\.mp4)',

            webpage, "download_url"
        )
       
        download_url = self._html_search_regex(

            r'(https:\/\/5-337-10435-2.b.cdn13.com\/contents\/videos\/3000\/3032\/3032\.mp4\?.+)',

            webpage, "download_url"
        )
         '''
        download_url = self._html_search_regex(
            r'(https:\/\/cdn01\.metrotvnews\.com\/videos\/\d+\/\d+\/\d+\/\S+.mp4)',
            webpage, "download_url"
        )
        return {
            'id': video_id,
            'url': download_url,
            'title': title
        }
