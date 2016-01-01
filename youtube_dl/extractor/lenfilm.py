from .common import InfoExtractor
from re import match


class LenFilmIE(InfoExtractor):
	_VALID_URL = r'(?:https?://)?(?:www\.)?lenfilm\.tv/(?P<id>\w+)'

	def _real_extract(self, url):
		mobj = match(self._VALID_URL, url)
		video_id = mobj.group('id')
		webpage_url = u'http://www.lenfilm.tv/' + video_id
		webpage = self._download_webpage(webpage_url, video_id)
		downloadPageLink = self._html_search_regex(r'<a href="([^"]*)">[^<]*<div class="dalee">[^<]*<br/>[^<]*</div>[^<]*</a>[^<]*</div>', webpage, u'download_page')
		title = self._html_search_regex(r'<a href=".*#comm">(.*)<span class="yelow">.*</span>', webpage, u'title')
		self.report_extraction(title)
		downloadPage = self._download_webpage(downloadPageLink, video_id)
		video_url = self._html_search_regex(r'<a style="text-decoration:underline" id="dwl" href="([^"]*)', downloadPage, u'video URL')
		return {u'id':video_id,
		    u'url':video_url,
		    u'ext':'mp4',
			u'title':title}