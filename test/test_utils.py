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
		self.assertTrue(u'de' in sanitize_filename(u'abc/de'))
		self.assertFalse(u'/' in sanitize_filename(u'abc/de///'))

		self.assertEqual(u'abc_de', sanitize_filename(u'abc\\de'))
		self.assertEqual(u'abc_de', sanitize_filename(u'abc\\de'))
		self.assertTrue(u'de' in  sanitize_filename(u'abc\\de'))

		self.assertEqual(sanitize_filename(u'ä'), u'ä')
		self.assertEqual(sanitize_filename(u'кириллица'), u'кириллица')

	def test_ordered_set(self):
		self.assertEqual(orderedSet([1,1,2,3,4,4,5,6,7,3,5]), [1,2,3,4,5,6,7])
		self.assertEqual(orderedSet([]), [])
		self.assertEqual(orderedSet([1]), [1])
		#keep the list ordered
		self.assertEqual(orderedSet([135,1,1,1]), [135,1])

	def test_unescape_html(self):
		self.assertEqual(unescapeHTML(u"%20;"), u"%20;")
