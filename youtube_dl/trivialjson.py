"""trivialjson (https://github.com/phihag/trivialjson)"""

import re
def loads(s):
	s = s.decode('UTF-8')
	def raiseError(msg, i):
		raise ValueError(msg + ' at position ' + str(i) + ' of ' + repr(s) + ': ' + repr(s[i:]))
	def skipSpace(i, expectMore=True):
		while i < len(s) and s[i] in ' \t\r\n':
			i += 1
		if expectMore:
			if i >= len(s):
				raiseError('Premature end', i)
		return i
	def decodeEscape(match):
		esc = match.group(1)
		_STATIC = {
			'"': '"',
			'\\': '\\',
			'/': '/',
			'b': unichr(0x8),
			'f': unichr(0xc),
			'n': '\n',
			'r': '\r',
			't': '\t',
		}
		if esc in _STATIC:
			return _STATIC[esc]
		if esc[0] == 'u':
			if len(esc) == 1+4:
				return unichr(int(esc[1:5], 16))
			if len(esc) == 5+6 and esc[5:7] == '\\u':
				hi = int(esc[1:5], 16)
				low = int(esc[7:11], 16)
				return unichr((hi - 0xd800) * 0x400 + low - 0xdc00 + 0x10000)
		raise ValueError('Unknown escape ' + str(esc))
	def parseString(i):
		i += 1
		e = i
		while True:
			e = s.index('"', e)
			bslashes = 0
			while s[e-bslashes-1] == '\\':
				bslashes += 1
			if bslashes % 2 == 1:
				e += 1
				continue
			break
		rexp = re.compile(r'\\(u[dD][89aAbB][0-9a-fA-F]{2}\\u[0-9a-fA-F]{4}|u[0-9a-fA-F]{4}|.|$)')
		stri = rexp.sub(decodeEscape, s[i:e])
		return (e+1,stri)
	def parseObj(i):
		i += 1
		res = {}
		i = skipSpace(i)
		if s[i] == '}': # Empty dictionary
			return (i+1,res)
		while True:
			if s[i] != '"':
				raiseError('Expected a string object key', i)
			i,key = parseString(i)
			i = skipSpace(i)
			if i >= len(s) or s[i] != ':':
				raiseError('Expected a colon', i)
			i,val = parse(i+1)
			res[key] = val
			i = skipSpace(i)
			if s[i] == '}':
				return (i+1, res)
			if s[i] != ',':
				raiseError('Expected comma or closing curly brace', i)
			i = skipSpace(i+1)
	def parseArray(i):
		res = []
		i = skipSpace(i+1)
		if s[i] == ']': # Empty array
			return (i+1,res)
		while True:
			i,val = parse(i)
			res.append(val)
			i = skipSpace(i) # Raise exception if premature end
			if s[i] == ']':
				return (i+1, res)
			if s[i] != ',':
				raiseError('Expected a comma or closing bracket', i)
			i = skipSpace(i+1)
	def parseDiscrete(i):
		for k,v in {'true': True, 'false': False, 'null': None}.items():
			if s.startswith(k, i):
				return (i+len(k), v)
		raiseError('Not a boolean (or null)', i)
	def parseNumber(i):
		mobj = re.match('^(-?(0|[1-9][0-9]*)(\.[0-9]*)?([eE][+-]?[0-9]+)?)', s[i:])
		if mobj is None:
			raiseError('Not a number', i)
		nums = mobj.group(1)
		if '.' in nums or 'e' in nums or 'E' in nums:
			return (i+len(nums), float(nums))
		return (i+len(nums), int(nums))
	CHARMAP = {'{': parseObj, '[': parseArray, '"': parseString, 't': parseDiscrete, 'f': parseDiscrete, 'n': parseDiscrete}
	def parse(i):
		i = skipSpace(i)
		i,res = CHARMAP.get(s[i], parseNumber)(i)
		i = skipSpace(i, False)
		return (i,res)
	i,res = parse(0)
	if i < len(s):
		raise ValueError('Extra data at end of input (index ' + str(i) + ' of ' + repr(s) + ': ' + repr(s[i:]) + ')')
	return res
