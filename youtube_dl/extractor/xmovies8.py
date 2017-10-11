# coding: utf-8
from __future__ import unicode_literals

import re
import time
import operator

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    compat_urlparse,
    ExtractorError
)


def urljoin(*args):
    """
    Joins given arguments into a url. Trailing but not leading slashes are
    stripped for each argument.

    The urljoin in utils is not suitable for me.
    I do not want to join url with the base url.
    I only want to concat two paths without duplicate slashs
    """
    return "/".join(map(lambda x: str(x).rstrip('/'), args))


def evaluate_expression(expr):
    """Evaluate a Javascript expression for the challange and return its value"""
    stack = []
    ranges = []
    value = ""
    for index, char in enumerate(expr):
        if char == "(":
            stack.append(index + 1)
        elif char == ")":
            begin = stack.pop()
            if stack:
                ranges.append((begin, index))
    for subexpr in [expr[begin:end] for begin, end in ranges] or (expr,):
        num = 0
        for part in subexpr.split("[]"):
            num += expression_values[part]
        value += str(num)
    return int(value)


operator_functions = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
}


expression_values = {
    "": 0,
    "+": 0,
    "!+": 1,
    "+!!": 1,
}


class XMovies8IE(InfoExtractor):
    _USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:47.0) Gecko/20100101 Firefox/47.0'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?xmovies8\.(?:tv|es)/movie/
        (?P<id>[a-zA-Z\-\.0-9]+)/?
        (?P<isWatching>watching)?
        (?:\.html)?
        '''
    _TEST = {
        'url': 'https://xmovies8.es/movie/the-hitman-s-bodyguard-2017.58852',

        # 'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'md5': 'f72c89fe7ecc14c1b5ce506c4996046e',
        'info_dict': {
            'id': '24749',
            'title': "The Hitman's Bodyguard (2017)",
            'ext': 'mp4',
            'description': "The world's top bodyguard gets a new client, a hit man who must testify at the International Court of Justice. They must put their differences aside and work together to make it to the trial on time.",
            'thumbnail': 'https://img.xmovies88.stream/crop/215/310/media/imagesv2/2017/08/the-hitman-s-bodyguard-2017-poster.jpg',
            'formats': [{
                'format_id': '1287',
                'url': 'https://s4.ostr.tv/hls/qvsbfwjmnxblgwsztrb2a5mblc3lpikarb6xmlv774kcxkug6nhunwo5q6pa/index-v1-a1.m3u8',
                'manifest_url': 'https://s4.ostr.tv/hls/,qvsbfwjmnxblgwsztrb2a5mblc3lpikarb6xmlv774kcxkug6nhunwo5q6pa,.urlset/master.m3u8',
                'tbr': 1287.551,
                'ext': 'mp4',
                'fps': 23.974,
                'protocol': 'm3u8',
                'preference': None,
                'width': 1280,
                'height': 720,
                'vcodec': 'avc1.64001f',
                'acodec': 'mp4a.40.2'}]
        },
        'params': {
            'skip_download': True,
        }
    }

    def _extract_all(self, txt, rules, pos=0, values=None):
        """Calls extract for each rule and returns the result in a dict"""
        if values is None:
            values = {}
        for key, begin, end in rules:
            result, pos = self._extract(txt, begin, end, pos)
            if key:
                values[key] = result
        return values, pos

    def _extract(self, txt, begin, end, pos=0):
        """Extract the text between 'begin' and 'end' from 'txt'

        Args:
            txt: String to search in
            begin: First string to be searched for
            end: Second string to be searched for after 'begin'
            pos: Starting position for searches in 'txt'

        Returns:
            The string between the two search-strings 'begin' and 'end' beginning
            with position 'pos' in 'txt' as well as the position after 'end'.
            If at least one of 'begin' or 'end' is not found, None and the original
            value of 'pos' is returned

        Examples:
            extract("abcde", "b", "d")    -> "c" , 4
            extract("abcde", "b", "d", 3) -> None, 3
        """
        try:
            first = txt.index(begin, pos) + len(begin)
            last = txt.index(end, first)
            return txt[first:last], last + len(end)
        except ValueError:
            return None, pos

    def _solve_challenge(self, url, headers=None):
        try:
            self._request_webpage(
                url, None, note='Solving Challenge', headers=headers)
        except ExtractorError as ee:
            if not isinstance(ee.cause, compat_HTTPError) or ee.cause.code != 503:
                raise
            page = ee.cause.read().decode('utf-8')
            params = self._extract_all(page, (
                ('jschl_vc', 'name="jschl_vc" value="', '"'),
                ('pass', 'name="pass" value="', '"'),
            ))[0]
            params["jschl_answer"] = self._solve_jschl(url, page)
            time.sleep(4)
            # print("params : ", params)
            rst = self._request_webpage(
                urljoin(url, "/cdn-cgi/l/chk_jschl"), None, note='Downloading redirect page', headers=headers, fatal=False, query=params)
            return rst

    def _solve_jschl(self, url, page):
        """Solve challenge to get 'jschl_answer' value"""
        data, pos = self._extract_all(page, (
            ('var', ',f, ', '='),
            ('key', '"', '"'),
            ('expr', ':', '}')
        ))
        solution = evaluate_expression(data["expr"])
        variable = "{}.{}".format(data["var"], data["key"])
        vlength = len(variable)
        expressions = self._extract(page, "'challenge-form');", "f.submit();", pos)[0]
        for expr in expressions.split(";")[1:]:
            if expr.startswith(variable):
                func = operator_functions[expr[vlength]]
                value = evaluate_expression(expr[vlength + 2:])
                solution = func(solution, value)
            elif expr.startswith("a.value"):
                return solution + len(compat_urllib_parse_urlparse(url).netloc)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        isWatching = mobj.group('isWatching')

        # print("original :", url)
        base_url = compat_urlparse.urljoin(url, "/")
        # print("base :", base_url)
        parsed_url = compat_urllib_parse_urlparse(url)
        # print("after parsed:", parsed_url)
        headers = {
            'User-Agent': self._USER_AGENT,
            'Referer': 'http://' + parsed_url.netloc + '/',
        }
        self._solve_challenge(base_url, headers)
        try:
            path = urljoin(parsed_url.path, "watching.html") if not isWatching else parsed_url.path
            # print(compat_urlparse.urljoin(base_url, path))
            webpage = self._download_webpage(compat_urlparse.urljoin(base_url, path), video_id, headers=headers)
            title = self._html_search_regex(r'(?is)<meta[^>]+prop="name" content="([^"]+)', webpage, 'title', fatal=False)
            description = self._html_search_regex(r'(?is)<meta[^>]+prop="description" content="([^"]+)', webpage, 'description', fatal=False)
            # duration = self._html_search_regex(r'(?is)<meta[^>]+prop="duration" content="([^"]+)', webpage, 'duration', fatal=False)
            thumbnailUrl = self._html_search_regex(r'(?is)<link[^>]+prop="thumbnailUrl" href="([^"]+)', webpage, 'thumbnailUrl', fatal=False)

            player_id = self._html_search_regex(r'[^}]+else[^{]+{.*load_player\(\'(\d+)\'[^\)]*', webpage, 'player_id', fatal=False)
            movie_id = self._html_search_regex(r'<script[^>]+/javascript\"> var movie = { id: (\d+),', webpage, 'movie_id', fatal=False)

            # print(compat_urlparse.urljoin(base_url, "/ajax/movie/load_player_v3"))
            load_player_v3 = self._download_json(compat_urlparse.urljoin(base_url, "/ajax/movie/load_player_v3"), video_id, note="Downloading player v3", headers=headers, query={'id': player_id})

            # print(title)
            # print(player_id)
            # print(load_player_v3)
            # print(load_player_v3.get('value'))

            playlist = self._download_json(parsed_url.scheme + ":" + load_player_v3.get('value'), video_id, note="Downloading video format", headers=headers)
            # print(playlist)
            formats = None
            for play in playlist.get('playlist'):
                # print(play.get('file'))
                # m3u8_formats = self._extract_m3u8_formats(play.get('file'),video_id)
                formats = self._extract_m3u8_formats(play.get('file'), video_id, "mp4")
                # print(formats)

            self._sort_formats(formats)
            # print({
            #     'id': movie_id,
            #     'title': title,
            #     'ext': formats[0].get('ext'),
            #     'description': description,
            #     'thumbnail': thumbnailUrl,
            #     'formats': formats
            # })
            return {
                'id': movie_id,
                'title': title,
                'ext': formats[0].get('ext'),
                'description': description,
                'thumbnail': thumbnailUrl,
                'formats': formats
            }
        except ExtractorError as ee:
            if not isinstance(ee.cause, compat_HTTPError) or \
               ee.cause.code != 503:
                self.to_screen(ee.cause.read().decode('utf-8'))
                raise
