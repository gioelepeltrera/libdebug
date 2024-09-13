#
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2024 Roberto Alessandro Bertolini, Gabriele Digregorio, Gioele Peltrera.
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
from time import sleep
class BreakpointTest(unittest.TestCase):
    def setUp(self):
        self.d = debugger('riscv_binaries/breakpoint_test')
        self.exceptions = []

    def test_bps(self):
        def bp_random_function(d, bp):
            try:
                self.assertTrue(d.x0 == 0x010548)
            except Exception as e:
                self.exceptions.append(e)

        def bp_loop_end(d, bp):
            try:
                self.assertTrue(d.a5 == 45)
            except Exception as e:
                self.exceptions.append(e)

        self.d.start()
        self.d.b("random_function", bp_random_function)
        self.d.b(0x105a2, bp_loop_end)
        self.d.cont()
        self.d.kill()
        self.assertTrue(True)
        if self.exceptions:
            raise self.exceptions[0]

if __name__ == '__main__':
    unittest.main() 

