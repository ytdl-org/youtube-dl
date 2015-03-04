# -*- coding: utf-8 -*-

import re

from .common import PostProcessor
from ..utils import PostProcessingError


class MetadataFromTitlePPError(PostProcessingError):
    pass


class MetadataFromTitlePP(PostProcessor):
    def __init__(self, downloader, titleformat):
        self._titleformat = titleformat
        self._titleregex, self._attributes = self.fmtToRegex(titleformat)

    def fmtToRegex(self, fmt):
        """
        Converts a string like
           '%(title)s - %(artist)s'
        to a regex like
           '(?P<title>.+)\ \-\ (?P<artist>.+)'
        and a list of the named groups [title, artist]
        """
        lastpos = 0
        regex = ""
        groups = []
        # replace %(..)s with regex group and escape other string parts
        for match in re.finditer(r'%\((\w+)\)s', fmt):
            regex += re.escape(fmt[lastpos:match.start()])
            groupname = match.group(1)
            groups.append(groupname)
            regex += r'(?P<' + groupname + '>.+)'
            lastpos = match.end()
        if lastpos < len(fmt):
            regex += re.escape(fmt[lastpos:len(fmt)])
        return regex, groups

    def run(self, info):
        title = info['title']
        match = re.match(self._titleregex, title)
        if match is None:
            raise MetadataFromTitlePPError('Could not interpret title of video as "%s"' % self._titleformat)
        for attribute in self._attributes:
            value = match.group(attribute)
            info[attribute] = value
            self._downloader.to_screen('[fromtitle] parsed ' + attribute + ': ' + value)

        return True, info
