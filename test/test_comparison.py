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

"""
	Test the list of JSON expressions given on the following page
	Chosing a python JSON translator.
	http://blog.hill-street.net/?p=7
"""

from com.xhaus.jyson import *

def test_expression(ix, expr, human_readable=False):
	try:
		codec = JysonCodec
		expr = expr.replace("&N&", "\n")
		result = codec.loads(expr, strict_mode=False)
		if human_readable:
			print "%3d >>>%s<<<" % (ix, expr)
			print "\tResult: %s" % (result)
		else:
			print result
	except JSONDecodeError, jdx:
		if human_readable:
			print "%3d >>>%s<<<" % (ix, expr)
			print "\tError : %s" % (jdx.message)
		else:
			print jdx.message

def test_file_of_expressions(filename):
	f = open(filename, "rt")
	data = f.read()
	for ix, l in enumerate(data.split('\n')):
		test_expression(ix, l, False)
	f.close()

if __name__ == "__main__":
	test_file_of_expressions("comparison_expressions.json")
