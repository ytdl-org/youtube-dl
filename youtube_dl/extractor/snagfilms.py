from .common import InfoExtractor
from ..utils import js_to_json
from re import DOTALL

class SnagFilmsIE(InfoExtractor):
	_VALID_URL = r'(?:https?://)?(?:www.)?snagfilms\.com/films/title/(?P<display_id>.+?)(?:/|$)'
	_TEST = {
		'url': 'http://www.snagfilms.com/films/title/lost_for_life',
		'info_dict':
		{
			'id': '0000014c-de2f-d5d6-abcf-ffef58af0017',
			'display_id': 'lost_for_life',
			'ext': 'mp4',
			'title': 'Lost for Life',
			'duration': 4489,
			'description': 'In the United States, more than 2500 individuals are serving life-without-parole sentences for crimes they committed when they were seventeen years old or younger. Children as young as thirteen are among the thousands serving these sentences. Directed by Joshua Rof&eacute; (who spent four intensive years on the project), LOST FOR LIFE tells the stories of these individuals, their families and the families of juvenile murder victims. This searingly powerful documentary tackles this contentious issue from multiple perspectives and explores the complexity of the lives of those affected. What is justice when a kid kills? Can a horrific act place a life beyond redemption? Could you forgive?<br />',
			'categories': ['Documentary','Crime','Award Winning','Festivals']
		}
	}

	def _real_extract(self, url):
		display_id = self._search_regex(
			self._VALID_URL,
			url,
			'display_id',
			group='display_id'
		)
		webpage = self._download_webpage(url, display_id)

		json_data = self._parse_json(self._html_search_regex(
			r'"data":{"film":(?P<data>{.*?}})}',
			webpage,
			'data',
			group='data'
		), display_id)
		title = json_data['title']
		video_id = json_data['id']
		duration = int(json_data['duration'])
		description = json_data['synopsis']
		categories = [category['title'] for category in json_data['categories']]

		embed_webpage = self._download_webpage('http://www.snagfilms.com/embed/player?filmId=' + video_id, video_id)
		sources = self._parse_json(js_to_json(self._html_search_regex(
			r'sources: (?P<sources>\[.*?\])',
			embed_webpage,
			'sources',
			group='sources',
			flags=DOTALL
		)), video_id)

		formats = []
		for source in sources:
			if source['type'] == 'm3u8':
				formats.extend(self._extract_m3u8_formats(source['file'], video_id))
			else:
				formats.append({'url': source['file'],'ext': source['type'], 'resolution': source['label']})
		self._sort_formats(formats)

		return {
			'id': video_id,
			'display_id': display_id,
			'title': title,
			'duration': duration,
			'description': description,
			'categories': categories,
			'formats': formats,
		}
