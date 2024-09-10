#
# This file is part of libdebug Python library (https://github.com/gioelepeltrera/libdebug).
# Copyright (c) 2024 Gioele Peltrera.
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

class BasicTest(unittest.TestCase):
    def setUp(self):
        self.d = debugger("arm_binaries/basic_test")
        self.exceptions = []

    def test_registers(self):
        global hit_bp
        hit_bp = 0

        def bp_64(d, _):
            try:
                global hit_bp

                # Asserting the 64-bit registers (x0 to x14)
                self.assertTrue(d.x0 == 0x33445566778899aa)
                self.assertTrue(d.x1 == 0x1122334455667700)
                self.assertTrue(d.x2 == 0x2233445566770011)
                self.assertTrue(d.x3 == 0x3344556677001122)
                self.assertTrue(d.x4 == 0x4455667700112233)
                self.assertTrue(d.x5 == 0x5566770011223344)
                self.assertTrue(d.x6 == 0x6677001122334455)
                self.assertTrue(d.x7 == 0xaabbccdd11223344)
                self.assertTrue(d.x8 == 0xbbccdd11223344aa)
                self.assertTrue(d.x9 == 0xccdd11223344aabb)
                self.assertTrue(d.x10 == 0xdd11223344aabbcc)
                self.assertTrue(d.x11 == 0x1122334455667788)
                self.assertTrue(d.x12 == 0x2233445566778899)
                self.assertTrue(d.x13 == 0x33445566778899aa)
                self.assertTrue(d.x14 == 0x445566778899aabb)

                hit_bp += 1
            except Exception as e:
                self.exceptions.append(e)

        def bp_32(d, _):
            try:
                global hit_bp

                # Asserting the 32-bit registers (w0 to w14)
                self.assertTrue(d.w0 == 0x11223344)
                self.assertTrue(d.w1 == 0x22334455)
                self.assertTrue(d.w2 == 0x33445566)
                self.assertTrue(d.w3 == 0x44556677)
                self.assertTrue(d.w4 == 0x55667788)
                self.assertTrue(d.w5 == 0x66778899)
                self.assertTrue(d.w6 == 0x778899aa)
                self.assertTrue(d.w7 == 0x8899aabb)
                self.assertTrue(d.w8 == 0x99aabbcc)
                self.assertTrue(d.w9 == 0xaabbccdd)
                self.assertTrue(d.w10 == 0xbbccdd11)
                self.assertTrue(d.w11 == 0xccdd1122)
                self.assertTrue(d.w12 == 0xdd112233)
                self.assertTrue(d.w13 == 0x11223344)
                self.assertTrue(d.w14 == 0x22334455)

                hit_bp += 1
            except Exception as e:
                self.exceptions.append(e)

        self.d.start()
        # Set breakpoints at specific instructions using addresses from objdump
        self.d.b(0x4006c4, bp_64, True)  # Corrected address for 64-bit register instructions
        self.d.b(0x40073c, bp_32, True)  # Corrected address for 32-bit register instructions
        self.d.cont()
        self.d.kill()

        self.assertTrue(hit_bp == 2)

        if self.exceptions:
            raise self.exceptions[0]

if __name__ == '__main__':
    unittest.main()

