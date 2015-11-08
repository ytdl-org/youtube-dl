# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from hashlib import sha1
import re
from zlib import decompress


class tvpleIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<url>(?:www\.)?tvple\.com/(?P<id>[0-9]+))'
    _TEST = {
        'url': 'http://tvple.com/311090',
        'md5': '02e384fd3c3c6884e1bb997f6afd51e2',
        'info_dict': {
            'id': '311090',
            'ext': 'mp4',
            'uploader': '[디지털 드럭] 나비붙이',
            'uploader_id': 'jack1609',
            'title': '팜플렛으로 yee를 연주하는 김병만',
            'description': '자작입니다. 첫 조교..인가..? 조교라긴 애매하지만, 어쨋든 노래로 만드는 건 이번이 처음입니다.\n원본 영상 출처: https://www.youtube.com/watch?v=E4BPHBL35dE\nyee는 유튜브에 치면 원본 영상이 나오는데 다들 아시죠??? 저작권 문제가 될 경우는 지우겠습니다...\n\n병만로이드라고 불러야 하나??'
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _decode_tvple(self, key):
        """based on decompiled tvple player v2.50401"""
        # 1st key checker
        if((key[:4] != "feff") | (key[20:21] != "_")):
            self.report_warning("error:wrong key")

        # descramble key
        deckey = list(key[69:85])
        code = key[125:][::-1]

        # descrambling
        hexed = code.replace(deckey[5], "g").replace(deckey[4], "h").replace(deckey[3], "i").replace(deckey[2], "j").replace(deckey[1], "k").replace(deckey[6], deckey[5]).replace(deckey[7], deckey[4]).replace(deckey[8], deckey[3]).replace(deckey[9], deckey[2]).replace(deckey[10], deckey[1]).replace("g", deckey[6]).replace("h", deckey[7]).replace("i", deckey[8]).replace("j", deckey[9]).replace("k", deckey[10])
        decoded = hexed.decode("hex")

        # 2nd key checker
        if(sha1(decoded).hexdigest() != key[85:125]):
            self.report_warning("error:key checksum failed")
        return decoded

    def _convert_sub(self, misc, title, width, height):
        clouds = self._decode_tvple(misc).decode('utf-8')
        lines = re.findall(r'<item .*?</item>', clouds)

        asstemp1 = "[Script Info]\nTitle: %s\nScriptType: v4.00+\nWrapStyle: 0\nPlayResX: %d\nPlayResY: %d\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle:Default,Arial,14,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n\n" % (title, width, height)

        asstemp2 = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        for line in lines:
            reg = re.search(r'id="(.*)" x="(.*)" y="(.*)" pos="(.*)">(.*)<', line)
            sec = int(reg.group(4))
            starttime = "%02d:%02d:%02d.00" % (divmod(divmod(sec, 60)[0], 60)[0], divmod(divmod(sec, 60)[0], 60)[1], divmod(sec, 60)[1])
            endtime = "%02d:%02d:%02d.00" % (divmod(divmod(sec + 2, 60)[0], 60)[0], divmod(divmod(sec + 2, 60)[0], 60)[1], divmod(sec + 2, 60)[1])
            asstemp2 += "Dialogue: 0,%s,%s,Default,,0,0,0,,{\\an4\pos(%d,%d)}%s\n" % (starttime, endtime, int(reg.group(2)), int(reg.group(3)), reg.group(5))

        return(asstemp1 + asstemp2)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        playurl = self._html_search_regex(r'http://api.tvple.com/crossdomain.xml\n(.*)\n1', self._decode_tvple(re.search(r'data-key="(.*)"', webpage).group(1)), "playurl")
        playpage = self._download_webpage(playurl, "playurl_%d" % int(video_id))
        urls = re.findall(r'<url>(.*)</url>', self._decode_tvple(playpage))

        title = re.search("<h2.*title=\"(.*)\"", webpage).group(1)  # title
        uploader = re.search(r'personacon-sm".*/>\s*(.*)\s*</a>', webpage).group(1)  # username
        uploader_id = re.search(r'"/ch/(.*)/videos"', webpage).group(1)  # userid
        description = re.search(r'break-word">\s*(.*)\s*<button', webpage, re.DOTALL).group(1).replace(" <br />", "").replace("<br />", "").replace("\n            ", "")  # description
        resolution = re.search(r'fa-television"></i></span>\s*([0-9]*)x([0-9]*)\s*</li>', webpage)  # resolution
        # point = re.search(r'fa-bar-chart"></i></span>\s*(.*)p\s*</li>', webpage).group(1).replace(",", "")  # point?
        view_count = int(re.search(r'fa-play"></i></span>\s*(.*)\s*</li>', webpage).group(1).replace(",", ""))  # played
        duration = int(re.search(r'fa-video-camera"></i></span>\s*(\d*):(\d*)\s*</li>', webpage).group(1)) * 60 + int(re.search(r'fa-video-camera"></i></span>\s*(\d*):(\d*)\s*</li>', webpage).group(2))  # duration
        # date = re.search(r'<small>\s*(\d{4}-\d{2}-\d{2}) (\d{1,2}:\d{1,2}:\d{1,2}).*\s*</small>', webpage).group(1).replace("-", "")  # date FIXME-sometimes not working
        # time = re.search(r'<small>\s*(\d{4}-\d{2}-\d{2}) (\d{1,2}:\d{1,2}:\d{1,2}).*\s*</small>', webpage).group(2)  # time FIXME-sometimes not working
        categories = re.search(r'badge-info">(.*)</span>', webpage).group(1)  # categories
        tags = re.findall(r'"/tag/(.*)" class="tag user-added">', webpage)  # tags
        formats = [{
            'url': urls[0],
            'ext': 'mp4',
            'format_id': 'mp4_h264_aac',
            'width': int(resolution.group(1)),
            'height': int(resolution.group(2)),
            'no_resume': True
        }]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            # 'comment_count': comment_count,
            'formats': formats,
            'subtitles': {'ass': [{'ext': 'ass', 'data': self._convert_sub(decompress(self._request_webpage(urls[1], "clouds_xml").read()), "%s-%s" % (title, video_id), int(resolution.group(1)), int(resolution.group(2)))}]},
            'categories': categories,
            'tags': tags

            # TODO more properties (see youtube_dl/extractor/common.py)
        }
