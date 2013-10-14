# coding: utf-8

import re
import json
import urllib2

from time import time
from random import randint

from .common import InfoExtractor


class TudouIE(InfoExtractor):
	#_VALID_URL = r'(?:http://)?(?:www\.)?tudou\.com/((?:listplay|programs)/(?:view|(.+?)))|(?:albumplay)/(?:([^/]+)|([^/]+))(?:\.html)?'
	_VALID_URL = r'(?:http://)?(?:www\.)?tudou\.com/(((?:listplay|programs)/(?:view|(.+?)))|((?:albumplay)(?:/[^/]*)))/(?:([^/]+)|([^/]+))(?:\.html)?'
	_TEST = {
	u'url': u'http://www.tudou.com/listplay/zzdE77v6Mmo/2xN2duXMxmw.html',
	u'file': u'159448201.f4v',
	u'md5': u'140a49ed444bd22f93330985d8475fcb',
	u'info_dict': {
		u"title": u"卡马乔国足开大脚长传冲吊集锦"
		}
	}

	def _url_for_id(self, id, quality = None):
		info_url = "http://v2.tudou.com/f?id="+str(id)
		if quality:
			info_url += '&hd' + quality
		webpage = self._download_webpage(info_url, id, "Opening the info webpage")
		final_url = self._html_search_regex('>(.+?)</f>',webpage, 'video url')
		return final_url

	def get_page(self,url):
		request=urllib2.urlopen(url)
		html=request.read()
		content_type=request.headers.get('Content-Type')
		m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
		if m:
			encoding=m.group(1)
			html=html.decode(encoding,"replace")
			return html
		else:
			return None


	def isyouku(self,url):
		request=urllib2.urlopen(url)
		html=request.read()
		content_type=request.headers.get('Content-Type')
		m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
		if m:
			encoding=m.group(1)
			html=html.decode(encoding,"replace")
		vcode=re.search(r'vcode\s*[:=]\s*\'([^\']+)\'',html).group(1)
		title=re.search(r'kw\s*[:=]\s*[\'\"]([^\']+?)[\'\"]',html).group(1)
		if vcode:
			return (vcode,title)
		else:
			return None

	def downloadYouku_by_id(self,videoId,title):
		info=self.get_youkuinfo(videoId)
		result=[]
		urls,sizes=zip(*self.find_video(info,None))
		pattern=re.compile(r'/st/([^/]+)/')
		ext=str(re.search(pattern, urls[0]).group(1))
		for i,url in enumerate(urls):
			part_info={
					'id':i,
					'url':url,
					'ext':ext,
					'title':title,
					'thumbnail':None,
					}
			result.append(part_info)

		return result


	def get_youkuinfo(self,videoId):
		return json.loads(self.get_page('http://v.youku.com/player/getPlayList/VideoIDS/' + videoId + '/timezone/+08/version/5/source/out/Sc/2'))

	def find_video(self,info, stream_type = None):
		#key = '%s%x' % (info['data'][0]['key2'], int(info['data'][0]['key1'], 16) ^ 0xA55AA5A5)
		segs = info['data'][0]['segs']
		types = segs.keys()
		if not stream_type:
			for x in ['hd2', 'mp4', 'flv']:
				if x in types:
					stream_type = x
					break
			else:
				raise NotImplementedError()
		assert stream_type in ('hd2', 'mp4', 'flv')
		file_type = {'hd2': 'flv', 'mp4': 'mp4', 'flv': 'flv'}[stream_type]

		seed = info['data'][0]['seed']
		source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\\:._-1234567890")
		mixed = ''
		while source:
			seed = (seed * 211 + 30031) & 0xFFFF
			index = seed * len(source) >> 16
			c = source.pop(index)
			mixed += c

		ids = info['data'][0]['streamfileids'][stream_type].split('*')[:-1]
		vid = ''.join(mixed[int(i)] for i in ids)

		sid = '%s%s%s' % (int(time() * 1000), randint(1000, 1999), randint(1000, 9999))

		urls = []
		for s in segs[stream_type]:
			no = '%02x' % int(s['no'])
			url = 'http://f.youku.com/player/getFlvPath/sid/%s_%s/st/%s/fileid/%s%s%s?K=%s&ts=%s' % (sid, no, file_type, vid[:8], no.upper(), vid[10:], s['k'], s['seconds'])
			urls.append((url, int(s['size'])))
		return urls

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		video_id = mobj.group(2)
		if video_id is None:
				vcode,title=self.isyouku(url)
				if not vcode:
					print "Not transferring to Youku"
					return None
				return self.downloadYouku_by_id(vcode,title)

		webpage = self._download_webpage(url, video_id)
		title = re.search(",kw:\"(.+)\"",webpage)
		if title is None:
			title = re.search(",kw: \'(.+)\'",webpage)

		title = title.group(1)
		thumbnail_url = re.search(",pic: \'(.+?)\'",webpage)
		if thumbnail_url is None:
			thumbnail_url = re.search(",pic:\"(.+?)\"",webpage)
		thumbnail_url = thumbnail_url.group(1)

		segs_json = self._search_regex(r'segs: \'(.*)\'', webpage, 'segments')
		segments = json.loads(segs_json)
		# It looks like the keys are the arguments that have to be passed as
		# the hd field in the request url, we pick the higher
		quality = sorted(segments.keys())[-1]
		parts = segments[quality]
		result = []
		len_parts = len(parts)
		if len_parts > 1:
			self.to_screen(u'%s: found %s parts' % (video_id, len_parts))
		for part in parts:
			part_id = part['k']
			final_url = self._url_for_id(part_id, quality)
			ext = (final_url.split('?')[0]).split('.')[-1]
			part_info = {'id': part_id,
						  'url': final_url,
						  'ext': ext,
						  'title': title,
						  'thumbnail': thumbnail_url,
						  }
			result.append(part_info)

		return result
