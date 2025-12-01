#!/usr/bin/env python
# coding: utf-8
"""Tests module for longside/shortside format selector."""

from __future__ import unicode_literals

# Allow direct execution
if __name__ == '__main__':
    import os
    import sys
    repo_dir = os.path.abspath(os.path.join(__file__, '../' * 3))
    sys.path.insert(0, repo_dir)

import unittest

from youtube_dl.extractor import YoutubeIE
from test.test_YoutubeDL import YDL, TEST_URL, _make_result


default_common_video_properties = {
    'url': TEST_URL,
}


def prepare_formats_info_dict(sizes, common={}):
    """Convert sizes (id, width, height) to info_dict."""
    def make_one_format(size):
        d = default_common_video_properties.copy()
        (d['format_id'], d['width'], d['height']) = size
        d.update(common)
        return d

    info_dict = _make_result([make_one_format(size) for size in sizes])
    return info_dict


def pick_format_ids(sizes, criteria):
    """Check which size(s) match the criteria. Return their IDs."""
    ydl = YDL({'format': criteria})
    yie = YoutubeIE(ydl)
    info_dict = prepare_formats_info_dict(sizes)
    yie._sort_formats(info_dict['formats'])
    ydl.process_ie_result(info_dict.copy())
    picked_ids = [info['format_id'] for info in ydl.downloaded_info_dicts]
    return picked_ids


class TestFormatSelection(unittest.TestCase):
    """Tests class for longside/shortside format selector."""

    def test_fmtsel_criteria_longside_shortside(self):
        """Find largest video within upper limits."""
        # Feature request: https://github.com/ytdl-org/youtube-dl/issues/30737

        crit = {'tendency': '', 'short': '', 'long': ''}

        def verify_fmtsel(sizes, want):
            crit_all = crit['tendency'] + crit['short'] + crit['long']
            picked_ids = pick_format_ids(sizes, crit_all)
            self.assertEqual(','.join(picked_ids), want)

        sizes_h = [
            ('A', 256, 144,),
            ('B', 426, 240,),
            ('C', 640, 360,),
            ('D', 854, 480,),
        ]
        sizes_v = [(id, h, w) for (id, w, h) in sizes_h]
        self.assertEqual(sizes_v, [
            # This list is non-authoritative, merely for readers' reference.
            ('A', 144, 256,),
            ('B', 240, 426,),
            ('C', 360, 640,),
            ('D', 480, 854,),
        ])

        # def size_by_id(sizes, id):
        #     return next((s for s in sizes if s[0] == id))

        def verify_all_shapes_same(expected_id):
            verify_fmtsel(sizes_h, expected_id)
            verify_fmtsel(sizes_v, expected_id)

        # First, test with no criteria (still empty from initialization above):
        verify_fmtsel(sizes_h, 'A')

        crit['tendency'] = 'best'
        verify_all_shapes_same('D')

        crit['long'] = '[longside<=720]'
        verify_all_shapes_same('C')

        crit['long'] = '[longside<=420]'
        verify_all_shapes_same('A')

        def shortside_group_1(long, best):
            crit['long'] = long
            crit['short'] = '[shortside<=720]'
            verify_all_shapes_same(best)

            crit['short'] = '[shortside<=420]'
            verify_all_shapes_same('C')

            crit['short'] = '[shortside<=360]'
            verify_all_shapes_same('C')

            crit['short'] = '[shortside<360]'
            verify_all_shapes_same('B')

        shortside_group_1(long='', best='D')
        shortside_group_1(long='[longside<=720]', best='C')


if __name__ == '__main__':
    unittest.main()
