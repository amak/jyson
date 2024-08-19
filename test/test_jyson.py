#
# Copyright 2009-2012 Alan Kennedy
#
# Licensed under the Apache License, Version 2.0 (the "License"); 
# you may not use this file except in compliance with the License. 
# You may obtain a copy of the License at 
#
#    http://www.apache.org/licenses/LICENSE-2.0 
#
# Unless required by applicable law or agreed to in writing, software 
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
# See the License for the specific language governing permissions and 
# limitations under the License. 
#

import java
import sys
import types
import unittest

from com.xhaus.jyson import *

def compareObjectToDict(d, o):
	for k in d.keys():
		if not (o.has_key(k) and d[k] == o[k]):
			raise AssertionError("o is missing key '%s'(%s)" % (k, str(type(k))))
	for k in o.keys():
		if not (d.has_key(k) and d[k] == o[k]):
			raise AssertionError("o is missing key '%s'(%s)" % (k, str(type(k))))

def compareArrayToList(l, a):
	if len(l) != len(a):
		raise AssertionError("Arrays different length: %d != %d" % (len(l), len(a)))
	for ix in xrange(len(l)):
		if l[ix] != a[ix]:
			raise AssertionError("Arrays differ at element %d: %s != %s" % (ix, l[ix], a[ix]))

class MyTestClass:

	def __init__(self):
		self.i = 1
		self.f = 2.0
		self.s = 'Alan'
		self.json_text = """{"i":%d, "f":%lf, "s":"%s"}""" % (self.i, self.f, self.s)

	def __json__(self):
		return self.json_text

class JysonTest(unittest.TestCase):

	def setUp(self):
		self.codec = JysonCodec()
		self.codec.strict_mode = True
		self.decoder = self.codec.loads
		self.encoder = self.codec.dumps

	def assertObjectEqual(self, first, second):
		compareObjectToDict(first, second)

	def assertArrayEqual(self, first, second):
		compareArrayToList(first, second)

	def _makeArrayRepr(self, values):
		pieces = ["["]
		for v in values:
			if isinstance(v, types.StringType) or isinstance(v, types.UnicodeType):
				pieces.append('"%s"' % v)
			else:
				pieces.append(repr(v))
			pieces.append(', ')
		# Get rid of the last ", "
		pieces[-1] = "]"
		return "".join(pieces)

class TestCodecAPI(JysonTest):

	def _testMode(self, expected):
#		self.failUnlessEqual(self.codec.accept_any_top_level_datum, expected)
		self.failUnlessEqual(self.codec.accept_shell_style_comments, expected)
		self.failUnlessEqual(self.codec.accept_single_quoted_strings, expected)
		self.failUnlessEqual(self.codec.accept_hex_char_escapes, expected)
		self.failUnlessEqual(self.codec.accept_hexadecimal_integers, expected)
		self.failUnlessEqual(self.codec.accept_octal_integers, expected)
		self.failUnlessEqual(self.codec.accept_junk_after_data, expected)

	def estStrictModeIsDefault(self):
		self.codec = JysonCodec()
		self._testMode(False)

	def estStrictMode(self):
		self.codec = JysonCodec()
		self.codec.strict_mode = True
		self._testMode(False)

	def estPermissiveMode(self):
		self.codec = JysonCodec()
		self.codec.strict_mode = False
		self._testMode(True)

class TestStuffAfterMainObject(JysonTest):

	def testWhitespace(self):
		for ok_whitespace in [' ', '\t', '\n', '\r\n', '\r\n\r\n', ]:
			try:
				self.codec.loads("[]" + ok_whitespace)
			except JSONDecodeError, jde:
				self.fail("Acceptable whitespace after data should not have caused JSONDecodeError")

	def testStandardComment(self):
		for ok_comment in ['// Valid', '// Valid\\n', '/* Valid */', '/* Valid*/\r\n', ]:
			try:
				self.codec.loads("[]" + ok_comment)
			except JSONDecodeError, jde:
				self.fail("Acceptable comment >>>" +ok_comment+ "<<<after data should not have caused JSONDecodeError")

	def testInvalidComment(self):
		for bad_comment in ['/ Invalid', '/ Invalid\\n', '/* Invalid ', '/* Invalid\r\n', '# Invalid', ]:
			try:
				self.codec.loads("[]" + bad_comment)
			except JSONDecodeError, jde:
				pass
			else:
				self.fail("Bad comment >>>" +bad_comment+ "<<< after data should have caused JSONDecodeError")

	def testNonStandardComment(self):
		options = {'accept_shell_style_comments': True}
		for ok_comment in ['# Valid', '## Valid', '# Valid \r\n', ]:
			try:
				self.codec.loads("[]" + ok_comment, **options)
			except JSONDecodeError, jde:
				self.fail("Acceptable comment >>>" +ok_comment+ "<<< after data should not have caused JSONDecodeError")

	def testForbiddenData(self):
		for extra_data in ['""', '1', '1.0', '[]', '{}', 'null', 'true', 'false', ]:
			try:
				self.codec.loads("[] " + extra_data)
			except JSONDecodeError, jde:
				pass
			else:
				self.fail("Additional data >>>" +extra_data+ "<<< after main data should have caused JSONDecodeError")

	def testAcceptForbiddenData(self):
		options = {'accept_junk_after_data': True}
		for extra_data in ['""', '1', '1.0', '[]', '{}', 'null', 'true', 'false', ]:
			try:
				self.codec.loads("[] " + extra_data, **options)
			except JSONDecodeError, jde:
				self.fail("Additional data >>>" +extra_data+ "<<< after main data should NOT have caused JSONDecodeError with accept_junk_after_data ENABLED.")
			else:
				pass

class TestDecodeStrings(JysonTest):

	def testDecodeEmptyString(self):
		s = '[""]'
		obj = self.decoder(s)
		self.assertArrayEqual([""], obj)

	def testDecodeUnterminatedString(self):
		s = '["]'
		try:
			obj = self.decoder(s)
		except JSONDecodeError:
			pass
		else:
			self.fail("Unterminated string should have raised JSONDecodeError")

	def testDecodeSingleQuotedStringRaisesException(self):
		s = "['Alan Kennedy']"
		try:
			obj = self.decoder(s)
		except JSONDecodeError:
			pass
		else:
			self.fail("Single quoted string should have raised JSONDecodeError")

	def testDecodeEscapedCharacters(self):
		for char in r'bfnrt\"':
			jyson_string = '["\\%s"]' % char
			py_string = eval(jyson_string)
			try:
				jyson_result = self.decoder(jyson_string)
				self.failUnlessEqual(py_string, jyson_result)
			except JSONDecodeError:
				self.fail("Error parsing valid string >>>%s<<<" % jyson_string)

	def testDecodeIllegalEscapedCharacters(self):
		for char in "acdevACDEV":
			jyson_string = '["\\%s"]' % char
			py_string = eval(jyson_string)
			try:
				jyson_result = self.decoder(jyson_string)
			except JSONDecodeError:
				pass
			else:
				self.fail("Parsing string with illegal escapes %s should have failed" % repr(jyson_string))

	def testDecodeUnicodeString(self):
		unicode_string = r'"Al\u00e1in \u00d3 Cinn\u00E9ide"'
		expected_py_result = [eval('u%s' % unicode_string)]
		self.assertArrayEqual(expected_py_result, self.decoder('[%s]' % unicode_string))
				
	def testDecodeBadUnicodeCharacter(self):
		for bad_char in "Gg$Xx":
			jyson_string = '["\\u123%s"]' % bad_char
			try:
				jyson_result = self.decoder(jyson_string)
			except JSONDecodeError:
				pass
			else:
				self.fail("Invalid hex digit should have raised JSONDecodeError")

	def testDecodeHexEscapeRaisesException(self):
		s = '["Al\\xe1in \\xd3 Cinn\\xe9ide"]'
		try:
			obj = self.decoder(s)
		except JSONDecodeError:
			pass
		else:
			self.fail("String with hexadecimal escapes should have raised JSONDecodeError")

	def testDecodeOctalEscapeRaisesException(self):
		s = '["Al\\341in \\323 Cinn\\351ide"]'
		try:
			obj = self.decoder(s)
		except JSONDecodeError:
			pass
		else:
			self.fail("String with octal escapes should have raised JSONDecodeError")

class TestEncodeStrings(JysonTest):

	def testEncodeEmptyString(self):
		self.failUnlessEqual('""', self.encoder(''))

	def testEncodeJythonUnicodeString(self):
		# This is really a test of internal type comparison
		self.assertArrayEqual('["Hello World"]', self.encoder([u'Hello World']))

	def testEncodeEscapedCharacters(self):
		for char in "bfnrt\\":
			jyson_string = '["\\%s"]' % char
			py_object = eval(jyson_string)
			self.failUnlessEqual(jyson_string, self.encoder(py_object))

	def testEncodeStringWithUnicodeEscapes(self):
		py_string = u'Al\u00E1in \u00D3 Cinn\u00E9ide'
		actual = self.encoder(py_string)
		expected = u'"%s"' % py_string
		self.failUnlessEqual(actual, expected)

	def testEncodeStringWithUnicodeNames(self):
		u = u'\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
		self.failUnlessEqual(self.encoder(u), u'"\u03b1\u03a9"')

class TestSupplementaryCharacters(JysonTest):

	def testEncodeStringWithSurrogate(self):
		import jarray
		smiley_bytes = [-2, -1, -40, 61, -34, 7]
		smiley_byte_array = jarray.array(smiley_bytes, 'b')
		java_smiley_string = java.lang.String(smiley_byte_array, "UTF-16")
		jython_smiley_string = unicode(java_smiley_string)
		expected_ascii = u'"\\uD83D\\uDE07"'
		self.failUnlessEqual(self.encoder(jython_smiley_string, emit_ascii=1), expected_ascii)

	def testDecocdeThenEncodeStringWithSurrogate(self):
		original = '["This is a treble-clef' + '\\' + 'uD834' + '\\' + 'uDD1E, really"]'
		encoded = self.encoder(self.decoder(original))
		self.failUnlessEqual(original, encoded)

class TestStringOptions(JysonTest):

	def testSingleQuotedString(self):
		options = {'accept_single_quoted_strings': True}
		s = "['Alan Kennedy']"
		obj = self.decoder(s, **options)
		self.assertArrayEqual(['Alan Kennedy'], obj)

	def testHexEscape(self):
		options = {'accept_hex_char_escapes': True}
		s = "Al\\xe1in \\xd3 Cinn\\xe9ide"
		self.assertArrayEqual(self.decoder('["%s"]' % s, **options), [eval('"%s"' % s)])

	def testEncodeStringWithUnicodeEscapesToAscii(self):
		options = {'emit_ascii': True}
		py_string = u'Al\u00E1in \u00D3 Cinn\u00E9ide'
		js_string = u'Al\\u00E1in \\u00D3 Cinn\\u00E9ide'
		self.failUnlessEqual(self.encoder(py_string, **options), '"'+js_string+'"')

# NIST: http://physics.nist.gov/cuu/Constants/

avogadro = '6.0221415e23'
electron_mass = '9.1093826e-31'

class TestDecodeNumbers(JysonTest):

	def testDecodeZero(self):
		jyson_result = self.decoder('[0]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.IntType)
		self.failUnlessEqual(jyson_result[0], 0)

	def testDecodeInteger(self):
		jyson_result = self.decoder('[1]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.IntType)
		self.failUnlessEqual(jyson_result[0], 1)

	def testDecodePositiveInteger(self):
		jyson_result = self.decoder('[+1]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.IntType)
		self.failUnlessEqual(jyson_result[0], 1)

	def testDecodeMaxPositiveSigned32BitIntPlusOne(self):
		jyson_result = self.decoder('[2147483648]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.LongType)
		self.failUnlessEqual(jyson_result[0], 2147483648L)

	def testDecodeNegativeInteger(self):
		jyson_result = self.decoder('[-1]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.IntType)
		self.failUnlessEqual(jyson_result[0], -1)

	def testDecodeMinNegativeSigned32BitIntMinusOne(self):
		jyson_result = self.decoder('[-2147483649]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.LongType)
		self.failUnlessEqual(jyson_result[0], -2147483649L)

	def testDecodeFloat(self):
		jyson_result = self.decoder('[1.0]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.FloatType)
		self.failUnless((jyson_result[0] - 1.0) < 0.00000001)

	def testDecodePositiveFloat(self):
		jyson_result = self.decoder('[+1.0]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.FloatType)
		self.failUnless((jyson_result[0] - 1.0) < 0.00000001)

	def testDecodeNegativeFloat(self):
		jyson_result = self.decoder('[-1.0]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.FloatType)
		self.failUnless((jyson_result[0] + 1.0) < 0.00000001)

	def testDecodeFloatStartsWithZero(self):
		jyson_result = self.decoder('[0.1415927]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.FloatType)
		self.failUnless((jyson_result[0] - 0.1415927) < 0.00000001)

	def testDecodeFloatWithNoCharsBeforePoint(self):
		jyson_result = self.decoder('[.1415927]')
		self.failUnlessEqual(type(jyson_result), types.ListType)
		self.failUnlessEqual(type(jyson_result[0]), types.FloatType)
		self.failUnless((jyson_result[0] - 0.1415927) < 0.00000001)

	def testDecodeExponent(self):
		jyson_result = self.decoder('['+avogadro+']')
		self.failUnless((jyson_result[0] - float(avogadro)) < 0.00000001)
		jyson_result = self.decoder('['+avogadro.upper()+']')
		self.failUnless((jyson_result[0] - float(avogadro.upper())) < 0.00000001)

	def testDecodePositiveExponent(self):
		avogadro_plus = avogadro.replace('e23', 'e+23')
		jyson_result = self.decoder('['+avogadro_plus+']')
		self.failUnless((jyson_result[0] - float(avogadro_plus)) < 0.00000001)
		jyson_result = self.decoder('['+avogadro_plus.upper()+']')
		self.failUnless((jyson_result[0] - float(avogadro_plus.upper())) < 0.00000001)

	def testDecodeNegativeExponent(self):
		jyson_result = self.decoder('['+electron_mass+']')
		self.failUnless((jyson_result[0] - float(electron_mass)) < 0.00000001)
		jyson_result = self.decoder('['+electron_mass.upper()+']')
		self.failUnless((jyson_result[0] + float(electron_mass)) < 0.00000001)

	def testDecodeOctalIntegerRaisesException(self):
		try:
			jyson_result = self.decoder('[010]')
		except JSONDecodeError:
			pass
		else:
			self.fail("Octal integer should have raised exception in strict mode")

	def testDecodeHexadecimalIntegerRaisesException(self):
		try:
			jyson_result = self.decoder('[0x01]')
		except JSONDecodeError:
			pass
		else:
			self.fail("Hexadecimal integer should have raised exception in strict mode")

class TestEncodeNumbers(JysonTest):

	def testEncodeInteger(self):
		for v in [0, 1, 1L, 0x01, 01, -1, 2147483648L, -2147483649L]:
			self.failUnlessEqual(self.encoder(v), str(v))
		
	def testEncodeFloat(self):
		for v in [0.0, 1.0, +1.0, -1.0, float(avogadro), float(electron_mass)]:
			result = self.encoder(v)
			self.failUnless((float(result) - v) < 0.00000001)

class TestDecodeNumberOptions(JysonTest):

	def testDecodeOctalInteger(self):
		options = {'accept_octal_integers': True}
		jyson_result = self.decoder('[010]', **options)
		self.assertArrayEqual(jyson_result, [8])

	def testDecodeInvalidOctalInteger(self):
		options = {'accept_octal_integers': True}
		try:
			jyson_result = self.decoder('[08]', **options)
		except JSONDecodeError:
			pass
		else:
			self.fail("Invalid octal constant should raised JSONDecodeError")

	def testDecodeHexInteger(self):
		options = {'accept_hexadecimal_integers': True}
		for value in [ \
			'0x0', '0xA0', '0xA00', '0xA000', '0xabcdef', '0xABCDEF', \
			'0X0', '0XA0', '0XA00', '0XA000', '0Xabcdef', '0XABCDEF', \
			'0XFF', \
			]:
			jyson_result = self.decoder('[%s]' % value, **options)
			self.assertArrayEqual(jyson_result, [eval(value)])

	def testDecodeInvalidHexInteger(self):
		options = {'accept_hexadecimal_integers': True}
		for value in [ \
			'0x', '0X', '0xG', '0x123H', '0xAZ', '0XG', \
			]:
			try:
				jyson_result = self.decoder('[%s]' % value, **options)
			except JSONDecodeError:
				pass
			else:
				self.fail("Invalid hex constant should have raised JSONDecodeError")

class TestDecodeConstants(JysonTest):

	# Should this fail? True != 1
	# But in jython 2.2, True IS Py.One
	def testDecodeTrue21(self):
		jyson_result = self.decoder('[true]')
		self.failUnlessEqual(jyson_result, [1])

	def testDecodeTrue(self):
		jyson_result = self.decoder('[true]')
		self.failUnless(jyson_result[0] is True)

	# Should this fail? False != 0
	# But in jython 2.2, False IS Py.Zero
	def testDecodeFalse21(self):
		jyson_result = self.decoder('[false]')
		self.failUnlessEqual(jyson_result[0], 0)

	def testDecodeFalse(self):
		jyson_result = self.decoder('[false]')
		self.failUnless(jyson_result[0] is False)

	def testDecodeNull(self):
		jyson_result = self.decoder('[null]')
		self.failUnless(jyson_result[0] is None)

	def testDecodeMisspelledKeywords(self):
		bad_keywords = ['True', 'TRUE', 'False', 'FALSE', 'None', 'NONE', 'Null', 'NULL']
		for kw in bad_keywords:
			try:
				jyson_result = self.decoder("[%s]" % kw)
			except JSONDecodeError:
				pass
			else:
				self.fail("Keyword '%s' should NOT have been recognised" % kw)

class TestEncodeConstants(JysonTest):

	def testEncodeTrue(self):
		self.failUnlessEqual(self.encoder(True), 'true')

	def testEncodeFalse(self):
		self.failUnlessEqual(self.encoder(False), 'false')

	def testEncodeNull(self):
		self.failUnlessEqual(self.encoder(None), 'null')

class TestDecodeJysonObject(JysonTest):

	def testDecodeEmptyObject(self):
		test_string = "{}"
		test_object = self.decoder(test_string)
		self.assertObjectEqual({}, test_object)

	def testDecodeObjectWithString(self):
		test_string = """{"test_key": "test_value"}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value'}, test_object)

	def testDecodeObjectWithStringWithNewlines(self):
		test_string = """{\n"test_key"\r\n:\n "test_value"\r}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value'}, test_object)

	def testDecodeObjectWithMultipleKys(self):
		test_string = """{"test_key_0": "test_value_0","test_key_1": "test_value_1","test_key_2": "test_value_2"}"""
		test_object = self.decoder(test_string)
		for i in range(3):
			self.assertEqual(test_object['test_key_%d' % i], 'test_value_%d' % i)

	def testDecodeObjectWithIntegerKey(self):
		bad_keys = [
			('integer', 1),
			('float', 1.0),
			('complex', 1j),
			('tuple', (1,2)),
		]
		for type_name, key in bad_keys:
			test_string = """{%s: "test_value"}""" % str(key)
			try:
				test_object = self.decoder(test_string)
			except JSONDecodeError:
				pass
			else:
				self.fail("Decoding non-string ('%s') key should have raised JSONDecodeError" % type_name)

	def testDecodeObjectWithStringContainingBraces(self):
		test_string = """{"test_key": "test_value}"}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value}'}, test_object)

	def testDecodeObjectWithCstyleComment(self):
		test_string = """{"test_key": /* This is a valid C-style comment */ "test_value"}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value'}, test_object)

	def testDecodeObjectWithCstyleMultilineComment(self):
		test_string = """{"test_key": /* This\n is\n a\n valid\n C-style\n comment */ "test_value"}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value'}, test_object)

	def testDecodeObjectWithOnelineComment(self):
		test_string = """{"test_key": "test_value"// This is a valid one line comment \n}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value'}, test_object)

	def testDecodeObjectWithEmbeddedOnelineComment(self):
		test_string = """{"test_key": // This is a valid one line comment \n"test_value"}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value'}, test_object)

	def testDecodeObjectWithTwoSequentialOnelineComments(self):
		test_string = """{"test_key": // This is a valid one line comment \n //Followed by another one line comment\n "test_value"}"""
		test_object = self.decoder(test_string)
		self.assertObjectEqual({'test_key': 'test_value'}, test_object)

	def testDecodeObjectWithDoubleEmbeddedCstyleComment(self):
		test_string = """{"test_key": /* This is an /* invalid */ C-style comment */ "test_value"}"""
		try:
			test_object = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Embedded c-style comment should have raised JSONDecodeError")

	def testDecodeObjectWithNoStarCstyleComment(self):
		test_string = """{"test_key": /* This is an invalid C-style comment / "test_value"}"""
		try:
			test_object = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Unterminated c-style comment should have raised JSONDecodeError")

	def testDecodeObjectWithNoSlashCstyleComment(self):
		test_string = """{"test_key": /* This is an invalid C-style comment * "test_value"}"""
		try:
			test_object = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Unterminated c-style comment should have raised JSONDecodeError")

	def testDecodeObjectWithBadOnelineComment(self):
		test_string = """{"test_key": "test_value"/ This is an invalid one line comment \n}"""
		try:
			test_object = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Invalid one line comment should have raised JSONDecodeError")

	def testDecodeObjectMissingTerminator(self):
		test_string = """{"test_key": "test_value" """
		try:
			test_object = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Missing terminator on object should have raised JSONDecodeError")

	def testDecodeObjectIllegalTerminator(self):
		test_string = """{"test_key": "test_value" """
		for illegal_terminator in ['|', ']', '#', '\\', '/', '<', '>', '+', ]:
			try:
				test_object = self.decoder(test_string+illegal_terminator)
			except JSONDecodeError:
				pass
			else:
				self.fail("Illegal terminator " +illegal_terminator+ " on object should have raised JSONDecodeError")

	def testDecodeObjectWithSingleQuotedKey(self):
		try:
			test_object = self.decoder("""{'test_key':"test_value",}""")
		except JSONDecodeError:
			pass
		else:
			self.fail("Object with single quoted key should have raised exception")

	def testDecodeObjectWithDanglingComma(self):
		try:
			test_object = self.decoder("""{"test_key":"test_value",}""")
		except JSONDecodeError:
			pass
		else:
			self.fail("Object with dangling comma should have raised exception")

	def testDecodeObjectWithDanglingCommas(self):
		try:
			test_object = self.decoder("""{"test_key":"test_value",,}""")
		except JSONDecodeError:
			pass
		else:
			self.fail("Object with dangling commas should have raised exception")

class TestEncodeJysonObject(JysonTest):

	def testEncodeEmptyObject(self):
		obj = {}
		result = self.encoder(obj)
		self.failUnlessEqual("{}", result)

	def testEncodeObject(self):
		o = {}
		o['test_key'] = 'test_value'
		self.failUnlessEqual('{"test_key":"test_value"}', self.encoder(o))

	def testEncodeObjectWithNonAsciiKey(self):
		key = u'Al\u00E1in \u00D3 Cinn\u00E9ide'
		for k in [key, 
			"Al\341in \323 Cinn\351ide", 
			"Al\xe1in \xd3 Cinn\xe9ide"]:
			o = {}
			o[k] = 'test_value'
			self.failUnlessEqual('{"'+key+'":"test_value"}', self.encoder(o))

	def testEncodeObjectWithListValue(self):
		for value in [ [1,2,3,4], self.decoder("[1,2,3,4]"), ]:
			o = {}
			o['test_key'] = value
			self.failUnlessEqual('{"test_key":[1,2,3,4]}', self.encoder(o))

	def testEncodeObjectWithObjectValue(self):
		for value in [ {"nested_key": "nested_value"}, # a python dictionary
			self.decoder('{"nested_key": "nested_value"}'), # a JysonObject
			]:
			o = {}
			o['test_key'] = value
			self.failUnlessEqual('{"test_key":{"nested_key":"nested_value"}}', self.encoder(o))

	def testEncodeDictWithNonStringKeyRaisesException(self):
		for k in [0, 1.0, (), self.encoder, ]:
			try:
				newd = {k:'value'}
				result = self.encoder(newd)
			except JSONEncodeError:
				pass
			else:
				self.fail("Non string key '%s' should have raised exception" % str(k))

class TestEncodePythonObject(JysonTest):

	def testEncodeEmptyDict(self):
		self.failUnlessEqual("{}", self.encoder({}))

	def testEncodeDict(self):
		self.failUnlessEqual('{"test_key":"test_value"}', self.encoder({'test_key':'test_value'}))

	def testEncodeDictWithInvalidKeys(self):
		invalid_keys = [1, 1.0, (2,3), 1j, unittest, JysonTest]
		for k in invalid_keys:
			try:
				result = self.encoder({k:'value'})
			except JSONEncodeError:
				pass
			else:
				self.fail("Invalid JSON object key '%s' should have raised exception" % str(k))

	def testEncodeObjectWithConversionMethod(self):
		my_obj = MyTestClass()
		self.failUnlessEqual(my_obj.json_text, self.encoder(my_obj))

	def testEncodeFunctionRaisesException(self):
		try:
			result = self.encoder(int)
		except JSONEncodeError:
			pass
		else:
			self.fail("Encoding function should have raised exception: got '%s'" % result)

	def testEncodeMethodRaisesException(self):
		try:
			result = self.encoder(self.decoder)
		except JSONEncodeError:
			pass
		else:
			self.fail("Encoding method should have raised exception: got '%s'" % result)

	def testEncodeClassRaisesException(self):
		try:
			result = self.encoder(JysonTest)
		except JSONEncodeError:
			pass
		else:
			self.fail("Encoding class should have raised exception: got '%s'" % result)

	def testEncodeObjectWithoutConversionMethod(self):
		try:
			result = self.encoder(JysonTest)
		except JSONEncodeError:
			pass
		else:
			self.fail("Encoding class without conversion method should have raised exception: got '%s'" % result)

class TestEncodeSequence(JysonTest):

	def testEmptyList(self):
		py_object = []
		json_text = self.encoder(py_object)
		self.failUnlessEqual("[]", json_text)

	def testList(self):
		py_object = [1, 1L, 1.0, "Hello World", u"Hello World", ]
		json_text = self.encoder(py_object)
		self.failUnlessEqual("""[1,1,1.0,"Hello World","Hello World"]""", json_text)

	def testNestedList(self):
		py_object = [1, [1, 2, 3], 2, 3, ]
		json_text = self.encoder(py_object)
		self.failUnlessEqual("""[1,[1,2,3],2,3]""", json_text)

	def testEmptyTuple(self):
		py_object = ()
		json_text = self.encoder(py_object)
		self.failUnlessEqual("[]", json_text)

	def testList(self):
		py_object = (1, 1L, 1.0, "Hello World", u"Hello World", )
		json_text = self.encoder(py_object)
		self.failUnlessEqual("""[1,1,1.0,"Hello World","Hello World"]""", json_text)

	def testNestedTuple(self):
		py_object = (1, (1, 2, 3), 2, 3, )
		json_text = self.encoder(py_object)
		self.failUnlessEqual("""[1,[1,2,3],2,3]""", json_text)

class TestDecodeArray(JysonTest):

	def testEmptyArray(self):
		test_string = "[]"
		test_array = self.decoder(test_string)
		self.assertArrayEqual([], test_array)

	def _testArray(self, values):
		test_string = self._makeArrayRepr(values)
		test_array = self.decoder(test_string)
		self.assertArrayEqual(values, test_array)

	def testArrayWithStrings(self):
		self._testArray(["value1", "value2"])

	def testArrayWithNewlines(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace('[', '[\n')
		test_string = test_string.replace(',', '\r\n,\n')
		test_string = test_string.replace(']', '\r]')
		test_array = self.decoder(test_string)
		self.assertArrayEqual(values, test_array)

	def testArrayWithExtraComma(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(']', ',]')
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Array with dangling comma should have raised exception")

	def testArrayWithExtraCommas(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(']', ',,]')
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Consecutive commas in array should have caused JSONDecodeError: got %s" % str(test_array))

	def testArrayWithStringsContainingSquareBrackets(self):
		self._testArray(["value1]", "value2]"])

	def testArrayWithStringsContainingHashes(self):
		self._testArray(["value1#", "value2#"])

	def testArrayWithStringsContainingCommentSlashes(self):
		self._testArray(["value1//", "value2//"])

	def testArrayWithStringsContainingCommentStarts(self):
		self._testArray(["value1/*", "*/value2/*"])

	def testArrayWithStringsContainingCommentEnds(self):
		self._testArray(["value1*/", "value2*/"])

	def testArrayWithStringsContainingFullComments(self):
		self._testArray(["value1/* */", "value2/* */"])

	def testArrayWithVariousValues(self):
		self._testArray([1, 1.1, "Alan Kennedy", u"Al\u00e1in \u00d3 Cinn\u00e9ide"])

	def testArrayWithCstyleComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '/* This is a valid c-style comment */,')
		test_array = self.decoder(test_string)
		self.assertArrayEqual(values, test_array)

	def testArrayWithCstyleMultilineComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '/* This\n is\n a\n valid\n c-style\n multiline\n comment */,')
		test_array = self.decoder(test_string)
		self.assertArrayEqual(values, test_array)

	def testArrayWithOnelineComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '// This is a valid one line comment \n,')
		test_array = self.decoder(test_string)
		self.assertArrayEqual(values, test_array)

	def testArrayWithDoubleEmbeddedCstyleComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '/* This is an /* invalid */ C-style comment */ ,')
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Embedded c-style comment should have raised JSONDecodeError")

	def testArrayWithNoStarCstyleComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '/* This is an invalid C-style comment / ,')
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Unterminated c-style comment should have raised JSONDecodeError")

	def testArrayWithNoSlashCstyleComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '/* This is an invalid C-style comment * ,')
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Unterminated c-style comment should have raised JSONDecodeError")

	def testArrayWithBadOnelineComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '/ This is an invalid C-style comment\n,')
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Invalid one line comment should have raised JSONDecodeError")

	def testArrayWithShellStyleComment(self):
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(',', '# This is an (invalid) shell-style comment\n,')
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Shell style comment should have raised JSONDecodeError")

	def testArrayMissingTerminator(self):
		test_string = """ ["value1", "value2" """
		try:
			test_array = self.decoder(test_string)
		except JSONDecodeError:
			pass
		else:
			self.fail("Missing terminator on array should have raised JSONDecodeError")

	def testArrayIllegalTerminator(self):
		for illegal_terminator in ['|', '}', '#', '\\', '/', '<', '>', '+', ]:
			test_string = """ ["value1", "value2" """
			try:
				test_array = self.decoder(test_string+illegal_terminator)
			except JSONDecodeError:
				pass
			else:
				self.fail("Illegal terminator " +illegal_terminator+ " on array should have raised JSONDecodeError")

	def testArrayMalformed(self):
		for s in ['[', ']',]:
			try:
			    obj = self.decoder(s)
			except JSONDecodeError:
				pass
			else:
			    self.fail("Malformed array '%s' should have raised JSONDecodeError" % s)

class TestVariousOptions(JysonTest):

	def testShellStyleCommentsOption(self):
		# Set the option to accept shell style comments
		options = {'accept_shell_style_comments': True}
		values = ["value1", "value2"]
		test_string = self._makeArrayRepr(values)
		test_string = test_string.replace(']', '# This is a shell style comment\n]')
		test_array = self.decoder(test_string, **options)
		self.assertArrayEqual(values, test_array)

	def testSingleQuotedStringKey(self):
		# Set the option to accept single quoted strings
		options = {'accept_single_quoted_strings': True}
		test_string = """{'test_key':'test_value'}"""
		test_object = self.decoder(test_string, **options)
		self.assertEqual(self.encoder(test_object), test_string.replace("'", '"'))

	def testDecodeArrayWithDanglingComma(self):
		options = {'accept_dangling_commas': True}
		try:
			test_object = self.decoder("[1,2,3,]", **options)
			self.failUnlessEqual(test_object, [1,2,3])
		except JSONDecodeError:
			self.fail("Array with dangling comma should have NOT raised exception with accept_dangling_commas enabled")

	def testDecodeArrayWithDanglingCommas(self):
		options = {'accept_dangling_commas': True}
		try:
			# This should still fail; two dangling commas not acceptable
			test_object = self.decoder("[1,2,3,,]", **options)
		except JSONDecodeError:
			pass
		else:
			self.fail("Array with dangling commas should have raised exception, even with accept_dangling_commas enabled")

	def testDecodeArrayWithOnlyComma(self):
		options = {'accept_dangling_commas': True}
		try:
			# This should still fail; a list with a single comma is not acceptable
			test_object = self.decoder("[,]", **options)
		except JSONDecodeError:
			pass
		else:
			self.fail("Array with only commas should have raised exception, even with accept_dangling_commas enabled")

	def testDecodeObjectWithDanglingComma(self):
		options = {'accept_dangling_commas': True}
		try:
			test_object = self.decoder("""{"test_key":"test_value",}""", **options)
		except JSONDecodeError:
			self.fail("Object with dangling comma should have NOT raised exception with accept_dangling_commas enabled")
		else:
			pass

	def testDecodeObjectWithDanglingCommas(self):
		options = {'accept_dangling_commas': True}
		try:
			# This should still fail; two dangling commas not acceptable
			test_object = self.decoder("""{"test_key":"test_value",,}""", *options)
		except JSONDecodeError:
			pass
		else:
			self.fail("Object with dangling commas should have raised exception, even with accept_dangling_commas enabled")

	def testDecodeObjectWithOnlyComma(self):
		options = {'accept_dangling_commas': True}
		try:
			# This should still fail; an object with a single comma is not acceptable
			test_object = self.decoder("""{"test_key":"test_value",,}""", **options)
		except JSONDecodeError:
			pass
		else:
			self.fail("Object with dangling commas should have raised exception, even with accept_dangling_commas enabled")

if __name__ == "__main__":
	unittest.main()
