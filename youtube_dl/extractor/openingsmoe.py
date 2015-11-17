from .common import InfoExtractor

class OpeningsMoeIE(InfoExtractor):
	_VALID_URL = r'(?:http://)?(?:www\.)?openings\.moe/.*'
	_TEST = {
		u"url": u"http://openings.moe/?video=InstallLinux.webm", 
		u"md5": u"0197c23fb5124395a51d4bc483506d61", 
		u"info_dict": {
			u"id": "InstallLinux", 
			u"url": u"http://openings.moe/video/InstallLinux.webm", 
			u"ext": u"webm", 
			u"title": u"openings.moe", 
		}
	}
	
	def _real_extract(self, url):
		webpage = self._download_webpage(url, "")
		self.report_extraction("")
		
		video_id = self._html_search_regex(
			r'<source src="video/([^"]+).webm" type="video/webm">', 
			webpage, u"Video URL")
	
		return {
			u"id": video_id, 
			u"url": u"http://openings.moe/video/" + video_id + u".webm", 
			u"ext": u"webm", 
			u"title": u"openings.moe", 
		}
