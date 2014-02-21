# coding: utf-8

from .common import InfoExtractor

class BRIE(InfoExtractor):

    IE_DESC = u"Bayerischer Rundfunk Mediathek"
    _VALID_URL = r"^https?://(?:www\.)?br\.de/mediathek/video/(?:sendungen/)?(?:[a-z0-9\-]+\.html)$"
    _BASE_URL = u"http://www.br.de"

    _TESTS = []

    def _real_extract(self, url):
        page = self._download_webpage(url, None)
        xml_url = self._search_regex(r"return BRavFramework\.register\(BRavFramework\('avPlayer_(?:[a-f0-9-]{36})'\)\.setup\({dataURL:'(/mediathek/video/[a-z0-9/~_.-]+)'}\)\);", page, "XMLURL")
        xml = self._download_xml(self._BASE_URL + xml_url, None)

        videos = []
        for xml_video in xml.findall("video"):
            video = {}
            video["id"] = xml_video.get("externalId")
            video["title"] = xml_video.find("title").text
            video["formats"] = self._extract_formats(xml_video.find("assets"))
            video["thumbnails"] = self._extract_thumbnails(xml_video.find("teaserImage/variants"))
            video["thumbnail"] = video["thumbnails"][0]["url"]
            video["description"] = " ".join(xml_video.find("shareTitle").text.splitlines())
            video["uploader"] = xml_video.find("author").text
            video["upload_date"] = "".join(reversed(xml_video.find("broadcastDate").text.split(".")))
            video["webpage_url"] = xml_video.find("permalink").text
            videos.append(video)

        if len(videos) > 1:
            self._downloader.report_warning(u'found multiple videos; please'
                u'report this with the video URL to http://yt-dl.org/bug')
        return videos[0]

    def _extract_formats(self, assets):
        vformats = []
        for asset in assets.findall("asset"):
            if asset.find("downloadUrl") is None:
                continue
            vformat = {}
            vformat["url"] = asset.find("downloadUrl").text
            vformat["ext"] = asset.find("mediaType").text
            vformat["format_id"] = asset.get("type")
            vformat["width"] = int(asset.find("frameWidth").text)
            vformat["height"] = int(asset.find("frameHeight").text)
            vformat["resolution"] = "%ix%i" % (vformat["width"], vformat["height"])
            vformat["tbr"] = int(asset.find("bitrateVideo").text)
            vformat["abr"] = int(asset.find("bitrateAudio").text)
            vformat["vcodec"] = asset.find("codecVideo").text
            vformat["container"] = vformat["ext"]
            vformat["filesize"] = int(asset.find("size").text)
            vformat["preference"] = vformat["quality"] = -1
            vformat["format"] = "%s container with %i Kbps %s" % (vformat["container"], vformat["tbr"], vformat["vcodec"])
            vformats.append(vformat)
        self._sort_formats(vformats)
        return vformats

    def _extract_thumbnails(self, variants):
        thumbnails = []
        for variant in variants.findall("variant"):
            thumbnail = {}
            thumbnail["url"] = self._BASE_URL + variant.find("url").text
            thumbnail["width"] = int(variant.find("width").text)
            thumbnail["height"] = int(variant.find("height").text)
            thumbnail["resolution"] = "%ix%i" % (thumbnail["width"], thumbnail["height"])
            thumbnails.append(thumbnail)
        thumbnails.sort(key = lambda x: x["width"] * x["height"], reverse=True)
        return thumbnails
