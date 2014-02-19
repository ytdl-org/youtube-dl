from .common import InfoExtractor

from ..utils import (
    compat_str,
    ExtractorError,
)


class SubtitlesInfoExtractor(InfoExtractor):
    @property
    def _have_to_download_any_subtitles(self):
        return any([self._downloader.params.get('writesubtitles', False),
                    self._downloader.params.get('writeautomaticsub')])

    def _list_available_subtitles(self, video_id, webpage):
        """ outputs the available subtitles for the video """
        sub_lang_list = self._get_available_subtitles(video_id, webpage)
        auto_captions_list = self._get_available_automatic_caption(video_id, webpage)
        sub_lang = ",".join(list(sub_lang_list.keys()))
        self.to_screen(u'%s: Available subtitles for video: %s' %
                       (video_id, sub_lang))
        auto_lang = ",".join(auto_captions_list.keys())
        self.to_screen(u'%s: Available automatic captions for video: %s' %
                       (video_id, auto_lang))

    def extract_subtitles(self, video_id, webpage):
        """
        returns {sub_lang: sub} ,{} if subtitles not found or None if the
        subtitles aren't requested.
        """
        if not self._have_to_download_any_subtitles:
            return None
        available_subs_list = {}
        if self._downloader.params.get('writeautomaticsub', False):
            available_subs_list.update(self._get_available_automatic_caption(video_id, webpage))
        if self._downloader.params.get('writesubtitles', False):
            available_subs_list.update(self._get_available_subtitles(video_id, webpage))

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

    def _download_subtitle_url(self, sub_lang, url):
        return self._download_webpage(url, None, note=False)

    def _request_subtitle_url(self, sub_lang, url):
        """ makes the http request for the subtitle """
        try:
            sub = self._download_subtitle_url(sub_lang, url)
        except ExtractorError as err:
            self._downloader.report_warning(u'unable to download video subtitles for %s: %s' % (sub_lang, compat_str(err)))
            return
        if not sub:
            self._downloader.report_warning(u'Did not fetch video subtitles')
            return
        return sub

    def _get_available_subtitles(self, video_id, webpage):
        """
        returns {sub_lang: url} or {} if not available
        Must be redefined by the subclasses
        """

        # By default, allow implementations to simply pass in the result
        assert isinstance(webpage, dict), \
            '_get_available_subtitles not implemented'
        return webpage

    def _get_available_automatic_caption(self, video_id, webpage):
        """
        returns {sub_lang: url} or {} if not available
        Must be redefined by the subclasses that support automatic captions,
        otherwise it will return {}
        """
        self._downloader.report_warning(u'Automatic Captions not supported by this server')
        return {}
