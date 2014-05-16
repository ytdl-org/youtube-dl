from .mtv import MTVIE
import re
from ..utils import fix_xml_ampersands

class VH1IE(MTVIE):
    IE_NAME = u'vh1.com'
    _FEED_URL = 'http://www.vh1.com/player/embed/AS3/fullepisode/rss/'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        idoc = self._download_xml(
            self._FEED_URL + '?id=' + video_id, video_id,
            'Downloading info', transform_source=fix_xml_ampersands)
        return [self._get_video_info(item) for item in idoc.findall('.//item')]


class VH1EpisodeIE(VH1IE):
    _VALID_URL = r'https?://www\.vh1\.com/video/.+?/full-episodes/.+?/(?P<videoid>[^/]+)/playlist\.jhtml'
    _TESTS = [
        {
            u'url': u'http://www.vh1.com/video/metal-evolution/full-episodes/progressive-metal/1678612/playlist.jhtml',
            u'playlist': [
                {
                    u'info_dict': {
                        u'id': u'731565',
                        u'ext': u'mp4',
                        u'title': u'Metal Evolution: Ep. 11 Act 1',
                        u'description': u'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 12 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                    }
                },
                {
                    u'info_dict': {
                        u'id': u'731567',
                        u'ext': u'mp4',
                        u'title': u'Metal Evolution: Ep. 11 Act 2',
                        u'description': u'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                    }
                },

                {
                    u'info_dict': {
                        u'id': u'731568',
                        u'ext': u'mp4',
                        u'title': u'Metal Evolution: Ep. 11 Act 3',
                        u'description': u'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                    }
                },
                {
                    u'info_dict': {
                        u'id': u'731569',
                        u'ext': u'mp4',
                        u'title': u'Metal Evolution: Ep. 11 Act 4',
                        u'description': u'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                    }
                },
                {
                    u'info_dict': {
                        u'id': u'731570',
                        u'ext': u'mp4',
                        u'title': u'Metal Evolution: Ep. 11 Act 5',
                        u'description': u'Many rock academics have proclaimed that the truly progressive musicianship of the last 20 years has been found right here in the world of heavy metal, rather than obvious locales such as jazz, fusion or progressive rock. It stands to reason then, that much of this jaw-dropping virtuosity occurs within what\'s known as progressive metal, a genre that takes root with the likes of Rush in the \'70s, Queensryche and Fates Warning in the \'80s, and Dream Theater in the \'90s. Since then, the genre has exploded with creativity, spawning mind-bending, genre-defying acts such as Tool, Mastodon, Coheed And Cambria, Porcupine Tree, Meshuggah, A Perfect Circle and Opeth. Episode 11 looks at the extreme musicianship of these bands, as well as their often extreme literary prowess and conceptual strength, the end result being a rich level of respect and attention such challenging acts have brought upon the world of heavy metal, from a critical community usually dismissive of the form.'
                    }
                }
            ]
        }
    ]


class VH1ClipIE(VH1IE):
    _VALID_URL = r'https?://www\.vh1\.com/video/misc/.+?/.+?\.jhtml#id=(?P<videoid>[^/]+)$'
    _TESTS = [
        {
            u'url': u'http://www.vh1.com/video/misc/706675/metal-evolution-episode-1-pre-metal-show-clip.jhtml#id=1674118',
            u'info_dict': {
                u'id': u'706675',
                u'ext': u'mp4',
                u'title': u'Metal Evolution: Episode 1 Pre-Metal Show Clip',
                u'description': u'The greatest documentary ever made about Heavy Metal begins as our host Sam Dunn travels the globe to seek out the origins and influences that helped create Heavy Metal. Sam speaks to legends like Kirk Hammett, Alice Cooper, Slash, Bill Ward, Geezer Butler, Tom Morello, Ace Frehley, Lemmy Kilmister, Dave Davies, and many many more. This episode is the prologue for the 11 hour series, and Sam goes back to the very beginning to reveal how Heavy Metal was created.'
            }
        }
    ]


class VH1ShortUrlIE(VH1IE):
    _VALID_URL = r'https?://www\.vh1\.com/video/play.jhtml\?id=(?P<videoid>[^/]+)$'
    _TESTS = [
        {
            u'url': u'http://www.vh1.com/video/play.jhtml?id=1678353',
            u'info_dict': {
                u'id': u'730355',
                u'ext': u'mp4',
                u'title': u'Metal Evolution: Episode 11 Progressive Metal Sneak',
                u'description': u'In Metal Evolution\'s finale sneak, Sam sits with Michael Giles of King Crimson and gets feedback from Metallica guitarist Kirk Hammett on why the group was influential.'
            }
        }
    ]


class VH1MusicVideoIE(VH1IE):
    _VALID_URL = r'https?://www\.vh1\.com/video/.+?/(?P<videoid>[^/]+)/.+?$'
    _TESTS = [
        {
            u'url': u'http://www.vh1.com/video/macklemore-ryan-lewis/900535/cant-hold-us-ft-ray-dalton.jhtml',
            u'info_dict': {
                u'id': u'900535',
                u'ext': u'mp4',
                u'title': u'Macklemore & Ryan Lewis - "Can\'t Hold Us ft. Ray Dalton"',
                u'description': u'The Heist'
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        # difference from VH1IE._real_extract() is "vid" param instead of "id"
        idoc = self._download_xml(
            self._FEED_URL + '?vid=' + video_id, video_id,
            'Downloading info', transform_source=fix_xml_ampersands)
        return [self._get_video_info(item) for item in idoc.findall('.//item')]
