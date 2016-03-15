# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re
import time
from datetime import datetime


class TvpleIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<url>(?:www\.)?tvple\.com/(?P<id>[0-9]+))'
    _TESTS = [{
        'url': 'http://tvple.com/311090',
        'md5': '46329fca94a29b5517a30d7e88f48dbf',
        'info_dict': {
            'id': '311090',
            'ext': 'mp4',
            'uploader': '[디지털 드럭] 나비붙이',
            'uploader_id': 'jack1609',
            'title': '팜플렛으로 yee를 연주하는 김병만',
            'description': '자작입니다. 첫 조교..인가..? 조교라긴 애매하지만, 어쨋든 노래로 만드는 건 이번이 처음입니다.\n원본 영상 출처: https://www.youtube.com/watch?v=E4BPHBL35dE\nyee는 유튜브에 치면 원본 영상이 나오는데 다들 아시죠??? 저작권 문제가 될 경우는 지우겠습니다...\n\n병만로이드라고 불러야 하나??',
            'duration': 9,
            'upload_date': '20150531',
            'timestamp': 1433094762
        }
    }, {
        'url': 'http://tvple.com/208230',
        'md5': '98e4f705fbb77b0ad9afe6e86751d89a',
        'info_dict': {
            'id': '208230',
            'ext': 'mp4',
            'uploader': 'mesenghe',
            'uploader_id': 'mesenghe',
            'title': '소환사 협곡의 개새끼',
            'description': 'http://youtu.be/LGABUervp48\n재밌게 봐라\n유튜브나 네이버 동영상으로 퍼가지 말고\n이젠 롤 관련된 건 안 만든다',
            'duration': 71,
            'upload_date': '20140927',
            'timestamp': 1411776051
        }
    }]

    def _convert_srt_subtitle(self, json, duration):
        """convert tvple subtitle to srt subtitle"""
        sec = []
        sub = ""
        timecode = []
        text = []
        for i in json:
            if(i != 'status'):
                sec.append(int(i))

        sec.sort()
        for second in sec:
            msec = []
            for i in json[str(second)]:
                msec.append(int(i))
            msec.sort()
            for millisecond in msec:
                timecode.append("%02d:%02d:%02d,%03d" % (second // 60 // 60, second // 60 % 60, second % 60, millisecond))
                text.append(json[str(second)][str(millisecond)].replace('<BR>', '\n').replace('&nbsp;', ''))

        timecode.append("%02d:%02d:%02d,%03d" % (duration // 60 // 60, duration // 60 % 60, duration % 60, int(("%0.3f" % duration)[-3:])))

        for i in range(1, len(timecode)):
            sub += str(i) + '\n' + timecode[i - 1] + ' --> ' + timecode[i] + '\n' + text[i - 1] + '\n\n'
        return sub

    def _convert_ass_cloud(self, json, videoid, title, width, height):
        """convert tvple cloud to ass subtitle"""
        sec = []

        asstemp1 = "[Script Info]\nTitle: %s\nScriptType: v4.00+\nWrapStyle: 0\nPlayResX: %d\nPlayResY: %d\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,14,&H23FFFFFF,&H000000FF,&HC8000000,&HC8000000,-1,0,0,0,100,100,0,0,1,2,2,5,10,10,10,1\n\n" % (title + '-' + videoid, width, height)

        for i in json:
            if(i != '_warning'):
                sec.append(int(i))

        sec.sort()

        asstemp2 = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

        for second in sec:
            for subs in json[str(second)]:
                timecodea = "%02d:%02d:%02d.00" % (second // 60 // 60, second // 60 % 60, second % 60)
                timecodeb = "%02d:%02d:%02d.00" % ((second + 2) // 60 // 60, (second + 2) // 60 % 60, (second + 2) % 60)
                asstemp2 += "Dialogue: 0,%s,%s,Default,,0,0,0,,{\\an4\pos(%d,%d)\\fad(0,50)}%s\n" % (timecodea, timecodeb, subs['x'] * width, subs['y'] * height, subs['text'])

        return (asstemp1 + asstemp2)

    def _get_subtitles(self, json, title, videoid, duration, width, height):
        subs = {}
        subs['tvple'] = []
        if json['cloud']['read_url'][0] != '':
            subs['tvple'].append({
                'ext': 'ass',
                'data': self._convert_ass_cloud(self._download_json(json['cloud']['read_url'], 'cloud_%d' % int(videoid)), videoid, title, width, height)
            })

        if json['subtitle'] != '':
            subs['tvple'].append({
                'ext': 'srt',
                'data': self._convert_srt_subtitle(self._download_json(json['subtitle'], 'subtitle_%d' % int(videoid)), duration)
            })

        return subs

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        playpage = self._download_json(re.search(r'data-meta="(.*)"', webpage).group(1), "playurl_%d" % int(video_id))

        title = re.search("<h2.*title=\"(.*)\"", webpage).group(1)  # title
        uploader = re.search(r'personacon-sm".*/>\s*(.*)\s*</a>', webpage).group(1)  # username
        uploader_id = re.search(r'"/ch/(.*)/videos"', webpage).group(1)  # userid
        description = re.search(r'collapse-content linkify break-word">\s*(.*)\s*<button type="button" class="collapse-button', webpage, re.DOTALL).group(1).replace(" <br />", "").replace("<br />", "").replace("\n            ", "")  # description
        view_count = int(re.search(r'fa-play"></i></span>\s*(.*)\s*</li>', webpage).group(1).replace(",", ""))  # played
        try:
            comment_count = int(re.search(r'fa-cloud"></i></span>\s*(\d*)개의 구름', webpage).group(1).replace(",", ""))  # comment count
        except AttributeError:  # if comment count is zero, tvple print '아직 구름이 없습니다. 첫 구름을 띄워보세요!'
            comment_count = 0

        duration = int(playpage['stream']['duration'])  # duration
        average_rating = int(re.search(r'fa-bar-chart"></i></span>\s*(.*)p\s*</li>', webpage).group(1).replace(",", ""))  # rating
        like_count = int(re.search(r'찜 하기\n<span class="badge">(\d*)</span>', webpage).group(1))  # liked

        uploadeddatetime = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})에 업로드됨', webpage)
        timestamp = time.mktime(datetime.strptime(uploadeddatetime.group(1), '%Y-%m-%d %H:%M:%S').timetuple()) + (60 * 60 * 9)  # timestamp + KST(+9)

        categories = re.search(r'badge-info">(.*)</span>', webpage).group(1)  # categories
        tags = re.findall(r'class="tag "\n.*}">(.*)</a>', webpage)  # tags

        formats = []
        for formatid in playpage['stream']['sources']:
            formats.append({
                'url': playpage['stream']['sources'][formatid]['urls']['mp4_avc'],
                'ext': 'mp4',  # tvple using mp4 for main format
                'format_id': formatid,
                'width': int(playpage['stream']['width']),
                'height': int(playpage['stream']['height'])
            })

        subtitles = self.extract_subtitles(playpage, title, video_id, duration, playpage['stream']['width'], playpage['stream']['height'])

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'comment_count': comment_count,
            'thumbnail': playpage['poster'],
            'formats': formats,
            'subtitles': subtitles,
            'categories': categories,
            'tags': tags,
            'timestamp': timestamp,
            'avrage_rating': average_rating,
            'like_count': like_count
        }
