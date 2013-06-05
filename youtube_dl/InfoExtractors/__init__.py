#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import


IEs = [
    ('Youtube', ['YoutubePlaylistIE', 'YoutubeChannelIE',
        'YoutubeUserIE', 'YoutubeSearchIE', 'YoutubeIE']),
    ('Generic', ['GenericIE']),
    ]


IE_list = []
for module, IE_names in IEs:
    _mod = __import__('youtube_dl.InfoExtractors.' + module,
        globals(), locals(), IE_names)
    for IE_name in IE_names:
        IE_list.append(getattr(_mod, IE_name))


def gen_extractors():
    """ Return a list of an instance of every supported extractor """
    return [ IE() for IE in IE_list ]

def get_info_extractor(IE_name):
    """Returns the info extractor class with the given ie_name"""
    return next(IE for IE in IE_list if IE.__name__ == IE_name + 'IE')
