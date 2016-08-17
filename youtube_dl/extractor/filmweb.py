from __future__ import unicode_literals

from .twentythreevideo import TwentyThreeVideoIE


class FilmwebIE(TwentyThreeVideoIE):
    IE_NAME = 'Filmweb'
    _VALID_URL = r'https?://(?:www\.)?filmweb\.no/trailere/article(?P<id>\d+).ece'
    _TEST = {
        'url': 'http://www.filmweb.no/trailere/article1264921.ece',
        'md5': 'e353f47df98e557d67edaceda9dece89',
        'info_dict': {
            'id': '1264921',
            'title': 'Det som en gang var',
            'ext': 'mp4',
            'description': 'Trailer: Scener fra et vennskap',
        }
    }

    _CLIENT_NAME = 'filmweb'
    _CLIENT_ID = '12732917'
    _EMBED_BASE_URL = 'http://www.filmweb.no/template/ajax/json_trailerEmbed.jsp?articleId=%s&autoplay=true'

    def _real_extract(self, url):
        article_id = self._match_id(url)
        webpage = self._download_webpage(url, article_id)

        title = self._search_regex(r'var\s+jsTitle\s*=\s*escape\("([^"]+)"\);',
            webpage, 'title', fatal=True)

        format_url = self._proto_relative_url(
            self._html_search_regex(r'"(//filmweb\.23video\.com/[^"]+)"',
                self._download_json(self._EMBED_BASE_URL % article_id,
                    article_id)['embedCode'], 'format url'))

        formats = self._extract_formats(format_url, self._CLIENT_ID)
        self._sort_formats(formats)

        return {
            'id': article_id,
            'title': title,
            'alt_title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }
