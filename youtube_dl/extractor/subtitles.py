from .common import InfoExtractor

from ..utils import (
    compat_str,
    ExtractorError,
)


class SubtitlesInfoExtractor(InfoExtractor):

    def _list_available_subtitles(self, video_id):
        """ outputs the available subtitles for the video """
        sub_lang_list = self._get_available_subtitles(video_id)
        sub_lang = ",".join(list(sub_lang_list.keys()))
        self.to_screen(u'%s: Available subtitles for video: %s' %
                       (video_id, sub_lang))

    def extract_subtitles(self, video_id, video_webpage=None):
        """ returns {sub_lang: sub} or {} if subtitles not found """
        if self._downloader.params.get('writesubtitles', False) or self._downloader.params.get('allsubtitles', False):
            available_subs_list = self._get_available_subtitles(video_id)
        elif self._downloader.params.get('writeautomaticsub', False):
            available_subs_list = self._get_available_automatic_caption(video_id, video_webpage)
        else:
            return None

        if not available_subs_list:  # error, it didn't get the available subtitles
            return {}
        if self._downloader.params.get('allsubtitles', False):
            sub_lang_list = available_subs_list
        else:
            if self._downloader.params.get('subtitleslangs', False):
                requested_langs = self._downloader.params.get('subtitleslangs')
            elif 'en' in available_subs_list:
                requested_langs = ['en']
            else:
                requested_langs = [list(available_subs_list.keys())[0]]

            sub_lang_list = {}
            for sub_lang in requested_langs:
                if not sub_lang in available_subs_list:
                    self._downloader.report_warning(u'no closed captions found in the specified language "%s"' % sub_lang)
                    continue
                sub_lang_list[sub_lang] = available_subs_list[sub_lang]

        subtitles = {}
        for sub_lang, url in sub_lang_list.items():
            subtitle = self._request_subtitle_url(sub_lang, url)
            if subtitle:
                subtitles[sub_lang] = subtitle
        return subtitles

    def _request_subtitle_url(self, sub_lang, url):
        """ makes the http request for the subtitle """
        try:
            sub = self._download_webpage(url, None, note=False)
        except ExtractorError as err:
            self._downloader.report_warning(u'unable to download video subtitles for %s: %s' % (sub_lang, compat_str(err)))
            return
        if not sub:
            self._downloader.report_warning(u'Did not fetch video subtitles')
            return
        return sub

    def _get_available_subtitles(self, video_id):
        """
        returns {sub_lang: url} or {} if not available
        Must be redefined by the subclasses
        """
        pass

    def _get_available_automatic_caption(self, video_id, webpage):
        """
        returns {sub_lang: url} or {} if not available
        Must be redefined by the subclasses that support automatic captions,
        otherwise it will return {}
        """
        self._downloader.report_warning(u'Automatic Captions not supported by this server')
        return {}
