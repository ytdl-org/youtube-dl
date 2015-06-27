from re import match,DOTALL
from .common import InfoExtractor
from ..utils import js_to_json

class SnagFilmsIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www.|embed.)?snagfilms\.com/(?:films/title/(?P<display_id>.+?)|embed/player\?.*filmId=(?P<id>.+?))(?:&|/|$)'
    _TESTS = [{
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
    },{
        'url': 'http://embed.snagfilms.com/embed/player?filmId=74849a00-85a9-11e1-9660-123139220831',
        'info_dict':
        {
            'id': '74849a00-85a9-11e1-9660-123139220831',
            'display_id': 'while_we_watch',
            'ext': 'mp4',
            'title': '#whilewewatch',
            'duration': 2311,
            'description': 'A gripping portrait of the Occupy Wall Street media revolution,&nbsp;#WHILEWEWATCH is the first definitive film to emerge from Zuccotti Park—with full access and cooperation from masterminds who made #OccupyWallStreet a reality.&nbsp;The #OccupyWallStreet media team had no fear of a critical city government, big corporations, hostile police or a lagging mainstream media to tell their story. Through rain, snow, grueling days and sleeping on concrete, they pump out exhilarating ideas to the world. With little money, they rely on Twitter, texting, Wi-Fi, posters, Tumblr, live streams, YouTube, Facebook, dramatic marches, drumbeats and chants. As the film unfolds, we witness the burgeoning power of social media.<br />',
            'categories': ['Documentary','Politics']
        }
    }]

    def _real_extract(self, url):
        display_id, video_id = match(self._VALID_URL,url).groups()
        if display_id is None:
            embed_webpage = self._download_webpage('http://www.snagfilms.com/embed/player?filmId=' + video_id, video_id)
            display_id = self._html_search_regex(
                r"snagfilms\.com/films/title/(?P<display_id>.+?)(?:/|')",
                embed_webpage,
                'display_id'
            )
        webpage = self._download_webpage('http://www.snagfilms.com/films/title/' + display_id, display_id)

        json_data = self._parse_json(self._html_search_regex(
            r'"data":{"film":(?P<data>{.*?}})}',
            webpage,
            'data'
        ), display_id)

        if video_id is None:
            video_id = json_data['id']
            embed_webpage = self._download_webpage('http://www.snagfilms.com/embed/player?filmId=' + video_id, video_id)

        title = json_data['title']
        duration = int(json_data['duration'])
        description = json_data['synopsis']
        categories = [category['title'] for category in json_data['categories']]
        thumbnail = json_data['image']

        sources = self._parse_json(js_to_json(self._html_search_regex(
            r'sources: (?P<sources>\[.*?\])',
            embed_webpage,
            'sources',
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
            'thumbnail': thumbnail,
            'formats': formats,
        }
