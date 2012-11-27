# -*- coding: utf-8 -*-

# Various small unit tests

import unittest

#from youtube_dl.utils import htmlentity_transform
from youtube_dl.utils import timeconvert
from youtube_dl.utils import sanitize_filename
from youtube_dl.utils import unescapeHTML
from youtube_dl.utils import orderedSet


class TestUtil(unittest.TestCase):
	def test_timeconvert(self):
		self.assertTrue(timeconvert('') is None)
		self.assertTrue(timeconvert('bougrg') is None)

	def test_sanitize_filename(self):
		self.assertEqual(sanitize_filename(u'abc'), u'abc')
		self.assertEqual(sanitize_filename(u'abc_d-e'), u'abc_d-e')

		self.assertEqual(sanitize_filename(u'123'), u'123')

		self.assertEqual(u'abc_de', sanitize_filename(u'abc/de'))
		self.assertFalse(u'/' in sanitize_filename(u'abc/de///'))

		self.assertEqual(u'abc_de', sanitize_filename(u'abc/<>\\*|de'))
		self.assertEqual(u'xxx', sanitize_filename(u'xxx/<>\\*|'))
		self.assertEqual(u'yes no', sanitize_filename(u'yes? no'))
		self.assertEqual(u'this - that', sanitize_filename(u'this: that'))

		self.assertEqual(sanitize_filename(u'AT&T'), u'AT&T')
		self.assertEqual(sanitize_filename(u'ä'), u'ä')
		self.assertEqual(sanitize_filename(u'кириллица'), u'кириллица')

		forbidden = u'"\0\\/'
		for fc in forbidden:
			for fbc in forbidden:
				self.assertTrue(fbc not in sanitize_filename(fc))

	def test_sanitize_filename_restricted(self):
		self.assertEqual(sanitize_filename(u'abc', restricted=True), u'abc')
		self.assertEqual(sanitize_filename(u'abc_d-e', restricted=True), u'abc_d-e')

		self.assertEqual(sanitize_filename(u'123', restricted=True), u'123')

		self.assertEqual(u'abc_de', sanitize_filename(u'abc/de', restricted=True))
		self.assertFalse(u'/' in sanitize_filename(u'abc/de///', restricted=True))

		self.assertEqual(u'abc_de', sanitize_filename(u'abc/<>\\*|de', restricted=True))
		self.assertEqual(u'xxx', sanitize_filename(u'xxx/<>\\*|', restricted=True))
		self.assertEqual(u'yes_no', sanitize_filename(u'yes? no', restricted=True))
		self.assertEqual(u'this_-_that', sanitize_filename(u'this: that', restricted=True))

		self.assertEqual(sanitize_filename(u'aäb中国的c', restricted=True), u'a_b_c')
		self.assertTrue(sanitize_filename(u'ö', restricted=True) != u'') # No empty filename

		forbidden = u'"\0\\/&: \'\t\n'
		for fc in forbidden:
			for fbc in forbidden:
				self.assertTrue(fbc not in sanitize_filename(fc, restricted=True))

		# Handle a common case more neatly
		self.assertEqual(sanitize_filename(u'大声带 - Song', restricted=True), u'Song')
		self.assertEqual(sanitize_filename(u'总统: Speech', restricted=True), u'Speech')
		# .. but make sure the file name is never empty
		self.assertTrue(sanitize_filename(u'-', restricted=True) != u'')
		self.assertTrue(sanitize_filename(u':', restricted=True) != u'')

	def test_ordered_set(self):
		self.assertEqual(orderedSet([1,1,2,3,4,4,5,6,7,3,5]), [1,2,3,4,5,6,7])
		self.assertEqual(orderedSet([]), [])
		self.assertEqual(orderedSet([1]), [1])
		#keep the list ordered
		self.assertEqual(orderedSet([135,1,1,1]), [135,1])

	def test_unescape_html(self):
		self.assertEqual(unescapeHTML(u"%20;"), u"%20;")
