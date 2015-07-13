from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
  parse_iso8601,
  strip_jsonp,
  js_to_json,
  float_or_none,
  int_or_none,
)
import re
from pprint import pprint

class YospaceIE(InfoExtractor):
    _VALID_URL = r'http://(?:csm-[a-z]|mas-[a-z]).cds\d+.yospace.com/(?P<type>csm|mas)/(?P<id>\d+/\d+)'
    _TESTS = [
        {
            'url': 'http://csm-e.cds1.yospace.com/csm/108986746/100312513735',
            'info_dict': {
                'id': '108986746_100312513735',
                'ext': 'mp4',
                'title': '108986746_100312513735',
                'description': None,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
    ]

    def _extract_m3u8(self, hls_url):
        formats = self._extract_m3u8_formats(hls_url, 'hls', 'mp4', m3u8_id='hls')
        return formats

    def _extract_formats(self, mas_url, video_id):
        formats = []
        hls_url = None
        jfpage = self._download_webpage(mas_url, video_id)
        jf = self._parse_json(jfpage, video_id, transform_source=js_to_json)
        for ent in jf:
           if ent.get('type','') == 'application/x-mpeg-url':
               hls_url = ent.get('url')
               formats.extend(self._extract_m3u8(hls_url))
           else:
               tbr = float_or_none(ent.get('size',0), 1000)
               if tbr == 0:
                  r = re.search(r'[\?\&]q=(\d+)', ent.get('url'))
                  if r:
                     tbr=float_or_none(r.group(1), 1)
               formats.append({
                   'url': ent.get('url'),
                   'format_id': ent.get('method','unknown')+'-'+ent.get('container','unknown'),
                   'protocol': ent.get('url').split(':')[0],
                   'tbr': tbr,
                   'ext': ent.get('container','unknown')
               })
        return formats

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url_type = mobj.group('type')
        display_id = url_type
        title = display_id
        formats = []
        hls_url = None

        if url_type == 'mas':
            mas_url = url.split('?')[0]+'?trans=json'
            formats = self._extract_formats(mas_url, video_id)
        else:
            hls_url = url

        if hls_url is not None:
            formats.extend(self._extract_m3u8(hls_url))


        self._sort_formats(formats)

        return {
            'id': video_id.replace('/','_'),
            'display_id': display_id,
            'title': video_id.replace('/','_'),
            'formats': formats,
        }

class ReutersIE(YospaceIE):
    _VALID_URL = r'http://(?:www\.)?reuters.com/.*?(?P<id>[^/]+)$'
    _TESTS = [
        {
            'url': 'http://www.reuters.com/article/2015/06/22/mideast-crisis-turkey-idINKBN0P21VN20150622',
            'info_dict': {
                'id': '364679847',
                'ext': 'mp4',
                'title': 'Refugees flood back into Syria from Turkey',
                'description': 'Thousands of Syrians have streamed back across the border from Turkey to their hometown, now liberated from Islamic State. Sean Carberry reports.',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.reuters.com/video/2015/07/10/mexican-volcano-spews-fire-and-ash?videoId=364911782',
            'info_dict': {
                'id': '364911782',
                'ext': 'mp4',
                'title': 'Mexican volcano spews fire and ash',
                'description': 'Mexico\'s Fire Volcano spews fire and ash as streams of lava run down its side. Rough Cut (no reporter narration).',
            },
            'params': {
                'skip_download': True,
            },
        },
    ]

    def _scrape_javascript(self,webpage):
        ret = []
        rdata = {}
        
        javascript_chunks = re.findall(r'<script[^>]+text/javascript[^>]*>(.*?)</script>',webpage,re.DOTALL)
        if not javascript_chunks:
            return
        def msub(m):
            s = m.group(1)
            if rdata.get(s):
                s = rdata.get(s)
                return ': "'+s+'",\n'
            return ': False,\n'
        vidnum = 0
        for innerhtml in javascript_chunks:
            drawplayer_js = re.search(r'Reuters.yovideo.drawPlayer\((\{[^\}]+://.+?\})\);',innerhtml,re.DOTALL);
            if drawplayer_js:
                vidnum += 1
                drawplayer_js = re.sub(r'".+?"\s*:\s*[^\d"\'].+?,\n','',drawplayer_js.group(1))
                vdata = self._parse_json(drawplayer_js, 'javascript chunk', transform_source=js_to_json)
                desc = re.search(r'var RTR_VideoBlurb\s*=\s*"(.+?)";',innerhtml,re.DOTALL)
                if desc:
                    vdata['description'] = desc.group(1)
                vdata['vidnum']=vidnum
                ret.append(vdata)
            else:
                if re.search(r'^\s*Reuters\.([^\s\[\]\.]+\.[^\[\]]+?)\s*=\s*[\'\"\d].+?;\s*\n',innerhtml,re.M):
                    js_vars = re.findall(r'^\s*Reuters\.([^\s\[\]\.]+\.[^\s\[\]\.]+)\s*=\s*[\'"]?(.*?)[\'"]?;\s*\n',innerhtml,re.M)
                    for ent in js_vars:
                        if re.search(r'["\'].+?[\(\)\+]',ent[1]):
                           continue
                        if not ent[1]:
                           continue
                        rdata[ent[0]] = ent[1]
                drawplayer_js = re.search(r'Reuters.yovideo.drawPlayer\((\{.+?\})\);',innerhtml,re.DOTALL);
                if drawplayer_js:
                   vidnum += 1
                   ds = drawplayer_js.group(1)
                   ds = re.sub(r':\s*Reuters\.([a-zA-Z_]+\.[a-zA-Z_]+)\s*,\s*\n',msub,ds)
                   # "stuff_with": "variables like "+this("breaks")+" js_to_json";
                   ds = re.sub(r'[\'"].+?[\'"]\s*:\s*\(.+,\s*\n','',ds)
                   vdata = self._parse_json(ds, 'parsed javascript chunk', transform_source=js_to_json)
                   vdata['vidnum']=vidnum
                   ret.append(vdata)
        return ret

    def _real_extract(self, url):
        from .yospace import YospaceIE
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        ret = []
        webpage = self._download_webpage(url, video_id)
        vids = self._scrape_javascript(webpage)
        for vid in vids:
           vurl = vid.get('flv',vid.get('mpeg'))
           if vurl:
              formats = []
              formats.append({
                  'url': vurl,
                  'format_id': 'embed-flv-'+str(vid.get('vidnum')),
                  'protocol': vurl.split(':')[0],
                  'width': int_or_none(vid.get('width')),
                  'height': int_or_none(vid.get('height')),
                  'ext': 'flv',
                  'tbr': 1080.0 if vid.get('vbc','vbcValue') == 'vbcValue' else float_or_none(vid.get('vbc')),
              })
              yo_id_str = re.search(r'yospace.+/(\d+)\?f=(\d+)',vurl)
              if yo_id_str:
                 yo_id = yo_id_str.group(1)+'/'+yo_id_str.group(2)
                 murl = 'http://mas-e.cds1.yospace.com/mas/'+yo_id+'?trans=json'
                 yurl = 'http://csm-e.cds1.yospace.com/csm/'+yo_id
                 formats.extend(self._extract_formats(murl, video_id))
              if formats:
                 self._sort_formats(formats)
                 ret.append({
                     'id': vid.get('id',video_id),
                     'title': vid.get('title',video_id),
                     'description': vid.get('description'),
                     'webpage_url': url,
                     'formats': formats,
                 })
        if not ret:
            raise ExtractorError('No video found', expected=True)
        if len(ret) > 1:
           return self.playlist_result(ret, video_id, 'reuters')
        return ret[0]


