from __future__ import unicode_literals

from .common import InfoExtractor


class TotalWebCastingIE(InfoExtractor):
    IE_NAME = 'totalwebcasting.com'
    _VALID_URL = r'https?://www\.totalwebcasting\.com/view/\?func=VOFF.*'
    _TEST = {
        'url': 'https://www.totalwebcasting.com/view/?func=VOFF&id=columbia&date=2017-01-04&seq=1',
        'info_dict': {
            'id': '270e1c415d443924485f547403180906731570466a42740764673853041316737548',
            'title': 'Real World Cryptography Conference 2017',
            'description': 'md5:47a31e91ed537a2bb0d3a091659dc80c',
        },
        'playlist_count': 6,
    }

    def _real_extract(self, url):
        params = url.split('?', 1)[1]
        webpage = self._download_webpage(url, params)
        aprm = self._search_regex(r"startVideo\('(\w+)'", webpage, 'aprm')
        VLEV = self._download_json("https://www.totalwebcasting.com/view/?func=VLEV&aprm=%s&style=G" % aprm, aprm)
        parts = []
        for s in VLEV["aiTimes"].values():
            n = int(s[:-5])
            if n == 99:
                continue
            if n not in parts:
                parts.append(n)
        parts.sort()
        title = VLEV["title"]
        entries = []
        for p in parts:
            VLEV = self._download_json("https://www.totalwebcasting.com/view/?func=VLEV&aprm=%s&style=G&refP=1&nf=%d&time=1&cs=1&ns=1" % (aprm, p), aprm)
            for s in VLEV["playerObj"]["clip"]["sources"]:
                if s["type"] != "video/mp4":
                    continue
                entries.append({
                    "id": "%s_part%d" % (aprm, p),
                    "url": "https:" + s["src"],
                    "title": title,
                })
        return {
            '_type': 'multi_video',
            'id': aprm,
            'entries': entries,
            'title': title,
            'description': VLEV.get("desc"),
        }
