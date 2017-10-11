# coding: utf-8
from __future__ import unicode_literals

import re, time,operator
from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    clean_html,
    urljoin,
    compat_urlparse,
    ExtractorError,
    sanitized_Request,
    update_Request
)
def urljoin(*args):
    """
    Joins given arguments into a url. Trailing but not leading slashes are
    stripped for each argument.
    """
    return "/".join(map(lambda x: str(x).rstrip('/'), args))
def cookie_to_dict(cookie):
    cookie_dict = {
        'name': cookie.name,
        'value': cookie.value,
    }
    if cookie.port_specified:
        cookie_dict['port'] = cookie.port
    if cookie.domain_specified:
        cookie_dict['domain'] = cookie.domain
    if cookie.path_specified:
        cookie_dict['path'] = cookie.path
    if cookie.expires is not None:
        cookie_dict['expires'] = cookie.expires
    if cookie.secure is not None:
        cookie_dict['secure'] = cookie.secure
    if cookie.discard is not None:
        cookie_dict['discard'] = cookie.discard
    try:
        if (cookie.has_nonstandard_attr('httpOnly') or
                cookie.has_nonstandard_attr('httponly') or
                cookie.has_nonstandard_attr('HttpOnly')):
            cookie_dict['httponly'] = True
    except TypeError:
        pass
    return cookie_dict
def evaluate_expression(expr):
    """Evaluate a Javascript expression for the challange and return its value"""
    stack = []
    ranges = []
    value = ""
    for index, char in enumerate(expr):
        if char == "(":
            stack.append(index+1)
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
        # 'info_dict': {
        #     'id': '36164052',
        #     'ext': 'flv',
        #     'title': '데일리 에이프릴 요정들의 시상식!',
        #     'thumbnail': 're:^https?://(?:video|st)img.afreecatv.com/.*$',
        #     'uploader': 'dailyapril',
        #     'uploader_id': 'dailyapril',
        #     'upload_date': '20160503',
        # },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }
    def _get_cv(self,ct, host_name):
        #ct = ct.replace('\n', '').replace('\r', '')
        #find all hidden form value
        hidden = re.findall('<input type="hidden" name="([^"]+)" value="([^\"]+)"', ct)
        hidden = '&'.join(map(lambda x:'='.join(x), hidden))
        # get challange endpoint url
        url = re.findall('<form id="[^"]+" action="([^"]+)" method="get">', ct)[0]
        # get var name
        # var t,r,a,f, kMuTlpA={"t":+((!+[]+!![]+!![]+[])+(!+[]+!![]+!![]+!![]+!![]+!![]))};
        _, n, m, v = re.findall('var (:?[^,]+,)+ ([^=]+)={"([^"]+)":([^}]+)};', ct, re.DOTALL)[0]
        v = self._calc_symbol(v)
        # call eval() to calc expression
        for op, arg in re.findall('%s\.%s(.)=([^;]+);' % (n, m), ct):
            v = eval('%d %s %d' % (v, op, self._calc_symbol(arg)))
        # t = re.findall('\+\s*([^\.]+)\.length', ct, re.DOTALL)[0]
        # print '%s\.innerHTML\s*=\s*"([^"])";' % t
        # new_len = len(re.findall('%s\.innerHTML\s*=\s*"([^"]+)";' % t, ct, re.DOTALL)[0])
        # here we assume the meaning of t in defintely hostname, cf may change in the future
        v += len(host_name)
        # get wait time
        wait = re.findall('}, (\d+)\);', ct, re.DOTALL)[0]
        return hidden, v, url, wait
    def _calc_symbol(self,s):
        _ = re.findall('\+?\(\(([^\)]+)\)\+\(([^\)]+)\)\)', s)
        #type 1 +((...)+(...)) 2-digit num
        if _:
            v1, v2 = map(self._calc_symbol, _[0])
            return int(str(v1)+str(v2))
        #type 2 plain
        else:
            # use look-up table to replace
            vmap = {'!':1, '[]':0, '!![]':1, '':0}
            return sum(map(lambda x:vmap[x], s.split('+')))
    def _pycfl(self,s):
        # !+[]  1
        # !![]  1
        # ![]   0
        # []    0
        result = ''
        # print(s)  # DEBUG
        ss = re.split('\(|\)', s)
        for s in ss:
            if s in ('+', ''):
                continue
            elif s[0] == '+':
                s = s[1:]
            s = s.replace('!+[]', '1')
            s = s.replace('!![]', '1')
            s = s.replace('![]', '0')
            s = s.replace('[]', '0')
            s = s.replace('+!![]', '10')
            result += str(sum([int(i) for i in s.split('+')]))
        return result

    def _extract_all(self,txt, rules, pos=0, values=None):
        """Calls extract for each rule and returns the result in a dict"""
        if values is None:
            values = {}
        for key, begin, end in rules:
            result, pos = self._extract(txt, begin, end, pos)
            if key:
                values[key] = result
        return values, pos
    def _extract(self,txt, begin, end, pos=0):
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
            return txt[first:last], last+len(end)
        except ValueError:
            return None, pos
    
    def _solve_challenge(self, req,headers=None):
        try:
            self._request_webpage(
                req, None, note='Solve Challenge',headers=headers)
        except ExtractorError as ee:
            if not isinstance(ee.cause, compat_HTTPError) or ee.cause.code != 503:
                raise
            page = ee.cause.read().decode('utf-8')
            params = self._extract_all(page, (
                ('jschl_vc', 'name="jschl_vc" value="', '"'),
                ('pass'    , 'name="pass" value="', '"'),
            ))[0]
            params["jschl_answer"] = self._solve_jschl(req.full_url, page)
            time.sleep(4)
            print("params : ",params)
            req = update_Request(req,urljoin(req.full_url,"/cdn-cgi/l/chk_jschl"),query=params)
            self._request_webpage(
                req, None, note='Downloading redirect page',headers=headers,fatal=False)
            return req
            # session.get(urllib.parse.urljoin(url, "/cdn-cgi/l/chk_jschl"), params=params)
            # return session.cookies
    def _solve_jschl(self,url, page):
        """Solve challenge to get 'jschl_answer' value"""
        data, pos = self._extract_all(page, (
            ('var' , ',f, ', '='),
            ('key' , '"', '"'),
            ('expr', ':', '}')
        ))
        solution = evaluate_expression(data["expr"])
        variable = "{}.{}".format(data["var"], data["key"])
        vlength = len(variable)
        expressions = self._extract(page, "'challenge-form');", "f.submit();", pos)[0]
        for expr in expressions.split(";")[1:]:
            if expr.startswith(variable):
                func = operator_functions[expr[vlength]]
                value = evaluate_expression(expr[vlength+2:])
                solution = func(solution, value)
            elif expr.startswith("a.value"):
                return solution + len(compat_urllib_parse_urlparse(url).netloc)
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        isWatching = mobj.group('isWatching')

        print("original :", url)
        # url = compat_urlparse.urljoin(url, "/watching") if not isWatching else url
        base_url = compat_urlparse.urljoin(url,"/")
        print("base :", base_url)
        parsed_url = compat_urllib_parse_urlparse(url)
        print("after parsed:", parsed_url)
        headers = {
            'User-Agent': self._USER_AGENT,
            # 'Cookie':'__cfduid='+cfduid,
            'Referer':'http://'+parsed_url.netloc+'/',
            # 'Host':parsed_url.netloc
        }
        req = sanitized_Request(base_url)
        self._solve_challenge(req,headers)
        try:
            
            path = urljoin(parsed_url.path,"watching.html") if not isWatching else parsed_url.path
            #print(path)
            print(compat_urlparse.urljoin(base_url,path))
            webpage = self._download_webpage(compat_urlparse.urljoin(base_url,path), video_id, headers=headers)
            # self.to_screen(webpage)
            # title = self._html_search_regex(r'<div class="info_movie(?:\sfull.*)[^<]+class="full desc.*<h1>(.+)</h1>',webpage,'title', fatal=False)
            # self.to_screen(webpage)
            
            title = self._html_search_regex(r'(?is)<meta[^>]+prop="name" content="([^"]+)',webpage,'title', fatal=False)
            description = self._html_search_regex(r'(?is)<meta[^>]+prop="description" content="([^"]+)',webpage,'description', fatal=False)
            duration = self._html_search_regex(r'(?is)<meta[^>]+prop="duration" content="([^"]+)',webpage,'duration', fatal=False)
            thumbnailUrl = self._html_search_regex(r'(?is)<link[^>]+prop="thumbnailUrl" href="([^"]+)',webpage,'thumbnailUrl', fatal=False)

            player_id = self._html_search_regex(r'[^}]+else[^{]+{.*load_player\(\'(\d+)\'[^\)]*',webpage,'player_id', fatal=False)
            movie_id = self._html_search_regex(r'<script[^>]+/javascript\"> var movie = { id: (\d+),',webpage,'movie_id', fatal=False)

            print(compat_urlparse.urljoin(base_url,"/ajax/movie/load_player_v3"))
            load_player_v3 = self._download_json(compat_urlparse.urljoin(base_url,"/ajax/movie/load_player_v3"),video_id,headers=headers,query={'id':player_id})

            print(title)
            print(player_id)
            print(load_player_v3)
            print(load_player_v3.get('value'))

            playlist = self._download_json(parsed_url.scheme+":"+load_player_v3.get('value'),video_id,headers=headers)
            print(playlist)
            formats = None
            for play in playlist.get('playlist'):
                print(play.get('file'))
                # m3u8_formats = self._extract_m3u8_formats(play.get('file'),video_id)
                formats = self._extract_m3u8_formats(play.get('file'),video_id,"mp4")
                print(formats)
            if not formats and error:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, error), expected=True)
            self._sort_formats(formats)
            print({
                'id': movie_id,
                'title': title,
                'ext':formats[0].get('ext'),
                'description': description,
                'thumbnail': thumbnailUrl,
                'formats': formats
            })
            return {
                'id': movie_id,
                'title': title,
                'ext':formats[0].get('ext'),
                'description': description,
                'thumbnail': thumbnailUrl,
                'formats': formats
            }
        except ExtractorError as ee:
            print("OOOOOO")
            print(ee)
            if not isinstance(ee.cause, compat_HTTPError) or \
               ee.cause.code != 503:
                self.to_screen(ee.cause.read().decode('utf-8'))
                raise
            redir_webpage = ee.cause.read().decode('utf-8')
            cfduid = self._get_cookies(parsed_url.netloc).get('__cfduid').value
            self._set_cookie(parsed_url.netloc,'__cfduid',cfduid)
            
            c, v, u, w = self._get_cv(redir_webpage, parsed_url.netloc)
            print(c,v,u,w)
            # action = self._search_regex(
            #     r'<form id="challenge-form" action="([^"]+)"',
            #     redir_webpage, 'Redirect form')
            # vc = self._search_regex(
            #     r'<input type="hidden" name="jschl_vc" value="([^"]+)"/>',
            #     redir_webpage, 'redirect vc value')
            # pwd = self._search_regex(
            #     r'<input type="hidden" name="pass" value="([^"]+)"/>',
            #     redir_webpage, 'redirect pass value')
            # av = re.search(
            #     r'a\.value = ([0-9]+)[+]([0-9]+)[*]([0-9]+);',
            #     redir_webpage)
            # init = re.search(
            #     r'''
            #     (?sx)setTimeout\((?:.)*var\s+(?:[a-z],)*\s+(?P<dict>[a-zA-Z]*)={\"(?P<key>[a-zA-Z]*)\":(?P<init>[\(\)!\[\]\+]*)
            #     '''
            # ,redir_webpage)

            # ans = int(self._pycfl(init.group('init')))
            # for content in re.finditer(r''+init.group('dict')+'\.'+init.group('key')+'(?P<oper>[+\-\*/])=(?P<val>[\(\)!\[\]\+]*);',redir_webpage):
            #     if '*' == content.group('oper'):
            #         ans *= int(self._pycfl(content.group('val')))
            #     elif '+' == content.group('oper'):
            #         ans += int(self._pycfl(content.group('val')))
            #     elif '-' == content.group('oper'):
            #         ans -= int(self._pycfl(content.group('val')))
            #     elif '/' == content.group('oper'):
            #         ans /= int(self._pycfl(content.group('val')))
            
            # ans += len(parsed_url.netloc)
            # confirm_url = (
            #     parsed_url.scheme + '://' + parsed_url.netloc +
            #     action + '?' +
            #     compat_urllib_parse_urlencode({
            #         'jschl_vc': vc,
            #         # 'pass': pwd,
            #         'jschl_answer': compat_str(ans)                  
            #         })
            # )
            try:
                time.sleep(int(w)//1000)
                urlh = self._request_webpage(
                    req, None, note='Downloading redirect page',headers=headers,fatal=False)
                # print('%s://%s%s?%s&jschl_answer=%s' % (parsed_url.scheme, parsed_url.netloc,u, c, v))
                # print(confirm_url)
                
                # webpage, url_handle = self._download_webpage_handle(
                    # confirm_url, None, 'Downloading login page',headers=headers)
                # webpage = self._download_webpage(
                #     confirm_url, video_id,
                #     note='Confirming after redirect',
                #     headers=headers)

                self.to_screen(webpage)
                # title = self._html_search_regex(r'<div class="info_movie(?:\sfull)?"[^>]+<div class="tit full"><h1>(.+?)</h1>', webpage, 'title', fatal=False)
                # print(title)
                return {
                    'id': video_id,
                    # 'title': title,
                    'description': self._og_search_description(webpage),
                    # 'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
                    # TODO more properties (see youtube_dl/extractor/common.py)
                }
            except ExtractorError as ee:
                if not isinstance(ee.cause, compat_HTTPError) or \
                    ee.cause.code != 503:
                    raise
                webpage = ee.cause.read().decode('utf-8')

