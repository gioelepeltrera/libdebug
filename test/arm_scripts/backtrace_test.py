#
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2024 Gabriele Digregorio, Gioele Peltrera.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import unittest 
from libdebug import debugger


class BacktraceTest(unittest.TestCase):
    def setUp(self):
        self.d = debugger("arm_binaries/backtrace_test")
        self.exceptions = []

    def test_backtrace(self):

        def check_main(d,b):
            try:
                backtrace = d.backtrace()
                self.assertIn('_start', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertEqual(backtrace, ['main+8'])
            except Exception as e:
                self.exceptions.append(e)

        def check_function1(d,b):
            try:
                backtrace = d.backtrace()
                self.assertIn('_start', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertEqual(backtrace, ['function1+8', 'main+12'])
            except Exception as e:
                self.exceptions.append(e)

        def check_function2(d,b):
            try:
                backtrace = d.backtrace()
                self.assertIn('_start', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertEqual(backtrace, ['function2+8', 'function1+16', 'main+12'])
            except Exception as e:
                self.exceptions.append(e)
        
        def check_function3(d,b):
            try:
                backtrace = d.backtrace()
                self.assertIn('_start', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertEqual(backtrace, ['function3+8', 'function2+24', 'function1+16', 'main+12'])
            except Exception as e:
                self.exceptions.append(e)

        def check_function4(d,b):
            try:
                backtrace = d.backtrace()
                self.assertIn('_start', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertEqual(backtrace, ['function4+8', 'function3+24', 'function2+24', 'function1+16', 'main+12'])
            except Exception as e:
                self.exceptions.append(e)
        
        def check_function5(d,b):
            try:
                backtrace = d.backtrace()
                self.assertIn('_start', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertIn('__libc_start_', backtrace.pop())
                self.assertEqual(backtrace, ['function5+8', 'function4+24', 'function3+24', 'function2+24', 'function1+16', 'main+12'])
            except Exception as e:
                self.exceptions.append(e)


        self.d.start()
        self.d.b('main+8', check_main)
        self.d.b('function1+8', check_function1, hardware_assisted=True)
        self.d.b('function2+8', check_function2, hardware_assisted=True)
        self.d.b('function3+8', check_function3, hardware_assisted=True)
        self.d.b('function4+8', check_function4, hardware_assisted=True)
        self.d.b('function5+8', check_function5, hardware_assisted=True)
        self.d.cont()
        self.d.kill()

        if self.exceptions:
            raise self.exceptions[0]


if __name__ == '__main__':
    unittest.main()