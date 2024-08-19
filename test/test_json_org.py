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

import glob
import os.path

from com.xhaus.jyson import *

codec = JysonCodec

def test_expected_fail(filename, json_expr):
	try:
		codec.loads(json_expr)
	except JSONDecodeError, jdx:
		return True
	else:
		print "Expected failure '%s' >>>%s<<< incorrectly passed" % (filename, json_expr)
		return False

def test_expected_pass(filename, json_expr):
	try:
		codec.loads(json_expr)
	except JSONDecodeError, jdx:
		print "Expected pass '%s' >>>%s<<< incorrectly failed: %s" % (filename, json_expr, str(jdx))
		return False
	else:
		return True

def execute_tests(directory):
	files = glob.glob("%s/*" % directory)
	num_test_passes = num_test_failures = 0
	for f in files:
		json_expr = open(f, "rt").read()
		pass_fail = f.find("pass") != -1
		if pass_fail:
			result = test_expected_pass(os.path.basename(f), json_expr)
		else:
			result = test_expected_fail(os.path.basename(f), json_expr)
		if result:
			num_test_passes += 1
		else:
			num_test_failures += 1
	print "Pass: %d" % num_test_passes
	print "Fail: %d" % num_test_failures

if __name__ == "__main__":
	execute_tests("json.org")
