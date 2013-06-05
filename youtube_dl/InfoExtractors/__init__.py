#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

"""
List here the InfoExtractors.
The order matter! URLs will be handled by the first IE to match.
List either the name of the file, like 'Foo', containing 'FooIE' or
a tuple like (FILENAME, [IE_name, IE_name, ...])
"""
IEs = [
    ('Youtube', ['YoutubePlaylistIE', 'YoutubeChannelIE',
        'YoutubeUserIE', 'YoutubeSearchIE', 'YoutubeIE']),
    'Generic',
    ]


IE_list = []
IE_dict = {}
for entry in IEs:
    if type(entry) == type(''):
        module, IE_names = entry, [entry + 'IE']
    else:
        module, IE_names = entry

    _mod = __import__('youtube_dl.InfoExtractors.' + module,
        globals(), fromlist=IE_names)

    for IE_name in IE_names:
        IE = getattr(_mod, IE_name)
        IE_list.append(IE)
        IE_dict[IE_name] = IE


def gen_extractors():
    """ Return a list of an instance of every supported extractor """
    return [ IE() for IE in IE_list ]

def get_info_extractor(IE_name):
    """Returns the info extractor class with the given ie_name"""
    return IE_dict[IE_name + 'IE']
