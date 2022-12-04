import json

from .common import InfoExtractor


class BlerpIE(InfoExtractor):
    IE_NAME = 'blerp'
    _VALID_URL = r'https?://(?:www\.)?blerp\.com/soundbites/(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'https://blerp.com/soundbites/6320fe8745636cb4dd677a5a',
        'info_dict': {
            'id': '6320fe8745636cb4dd677a5a',
            'title': 'Samsung Galaxy S8 Over the Horizon Ringtone 2016',
            'uploader': 'luminousaj',
            'uploader_id': '5fb81e51aa66ae000c395478',
            'ext': 'mp3',
            'keywords': 'samsung,galaxy,s8,over the horizon,2016,ringtone',
        }
    }, {
        'url': 'https://blerp.com/soundbites/5bc94ef4796001000498429f',
        'info_dict': {
            'id': '5bc94ef4796001000498429f',
            'title': 'Yee',
            'uploader': '179617322678353920',
            'uploader_id': '5ba99cf71386730004552c42',
            'ext': 'mp3',
            'keywords': 'YEE,YEET,wo ha haah catchy tune yee,yee'
        }
    }]

    _GRAPHQL_OPERATIONNAME = "webBitePageGetBite"
    _GRAPHQL_QUERY = "query webBitePageGetBite($_id: MongoID!) {\n  web {\n    biteById(_id: $_id) {\n      ...bitePageFrag\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment bitePageFrag on Bite {\n  _id\n  title\n  userKeywords\n  keywords\n  color\n  visibility\n  isPremium\n  owned\n  price\n  extraReview\n  isAudioExists\n  image {\n    filename\n    original {\n      url\n      __typename\n    }\n    __typename\n  }\n  userReactions {\n    _id\n    reactions\n    createdAt\n    __typename\n  }\n  topReactions\n  totalSaveCount\n  saved\n  blerpLibraryType\n  license\n  licenseMetaData\n  playCount\n  totalShareCount\n  totalFavoriteCount\n  totalAddedToBoardCount\n  userCategory\n  userAudioQuality\n  audioCreationState\n  transcription\n  userTranscription\n  description\n  createdAt\n  updatedAt\n  author\n  listingType\n  ownerObject {\n    _id\n    username\n    profileImage {\n      filename\n      original {\n        url\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  transcription\n  favorited\n  visibility\n  isCurated\n  sourceUrl\n  audienceRating\n  strictAudienceRating\n  ownerId\n  reportObject {\n    reportedContentStatus\n    __typename\n  }\n  giphy {\n    mp4\n    gif\n    __typename\n  }\n  audio {\n    filename\n    original {\n      url\n      __typename\n    }\n    mp3 {\n      url\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        data = {
            'operationName': self._GRAPHQL_OPERATIONNAME,
            'query': self._GRAPHQL_QUERY,
            'variables': {
                '_id': audio_id
            }
        }

        headers = {
            'Content-Type': 'application/json'
        }

        json_result = self._download_json('https://api.blerp.com/graphql',
                                          audio_id, data=json.dumps(data).encode('utf-8'), headers=headers)

        bite_json = json_result['data']['web']['biteById']

        info_dict = {
            'id': bite_json['_id'],
            'url': bite_json['audio']['mp3']['url'],
            'title': bite_json['title'],
            'uploader': bite_json['ownerObject']['username'],
            'uploader_id': bite_json['ownerObject']['_id'],
            'ext': 'mp3',
            'keywords': ",".join(bite_json['userKeywords'])
        }

        return info_dict
