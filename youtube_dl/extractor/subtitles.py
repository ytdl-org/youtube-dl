import socket

from .common import InfoExtractor

from ..utils import (
    compat_http_client,
    compat_urllib_error,
    compat_urllib_request,
    compat_str,
)


class SubtitlesIE(InfoExtractor):

    def report_video_subtitles_available(self, video_id, sub_lang_list):
        """Report available subtitles."""
        sub_lang = ",".join(list(sub_lang_list.keys()))
        self.to_screen(u'%s: Available subtitles for video: %s' %
                       (video_id, sub_lang))

    def _list_available_subtitles(self, video_id):
        sub_lang_list = self._get_available_subtitles(video_id)
        self.report_video_subtitles_available(video_id, sub_lang_list)

    def _extract_subtitles(self, video_id):
        """
        Return a dictionary: {language: subtitles} or {} if the subtitles
        couldn't be found
        """
        sub_lang_list = self._get_available_subtitles(video_id)
        if not sub_lang_list:  # error, it didn't get the available subtitles
            return {}

        if self._downloader.params.get('writesubtitles', False):
            if self._downloader.params.get('subtitleslang', False):
                sub_lang = self._downloader.params.get('subtitleslang')
            elif 'en' in sub_lang_list:
                sub_lang = 'en'
            else:
                sub_lang = list(sub_lang_list.keys())[0]
            if not sub_lang in sub_lang_list:
                self._downloader.report_warning(u'no closed captions found in the specified language "%s"' % sub_lang)
                return {}
            sub_lang_list = {sub_lang: sub_lang_list[sub_lang]}

        subtitles = {}
        for sub_lang, url in sub_lang_list.iteritems():
            subtitle = self._request_subtitle_url(sub_lang, url)
            if subtitle:
                subtitles[sub_lang] = subtitle
        return subtitles

    def _request_subtitle_url(self, sub_lang, url):
        try:
            sub = compat_urllib_request.urlopen(url).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to download video subtitles for %s: %s' % (sub_lang, compat_str(err)))
            return
        if not sub:
            self._downloader.report_warning(u'Did not fetch video subtitles')
            return
        return sub

    def _get_available_subtitles(self, video_id):
        """returns the list of available subtitles like this {lang: url} """
        """or {} if not available. Must be redefined by the subclasses."""
        pass

    def _request_automatic_caption(self, video_id, webpage):
        """Request automatic caption. Redefine in subclasses."""
        """returns a tuple of ... """
        # return [(err_msg, None, None)]
        pass
