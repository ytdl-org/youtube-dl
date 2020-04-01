from __future__ import unicode_literals

from .common import InfoExtractor


class likeeIE(InfoExtractor):



    _VALID_URL = r'(?:https?://)?(?:www\.)?likee\.com/@(?P<id>\w+[-0-9])*/video/[0-9]+'
    #print(1)
    #_TESTS = {
        # TODO: Implement

    #}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            r'http?://video\.like\.video/[A-Za-z0-9!_/=@#$%^&*(),.?:{}|<>]*', video_id
        )


        title = "video 1"
        download_url = self._html_search_regex(

            r'http?://video\.like\.video/[A-Za-z0-9!_/=@#$%^&*(),.?:{}|<>]*',

            webpage, "download_url"
        )




        return {
            'id': video_id,
            'url': download_url,
            'title': title
        }
