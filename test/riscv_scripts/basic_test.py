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
        self.d = debugger("riscv_binaries/basic_test")
        self.exceptions = []

    def test_registers(self):
        global hit_bp
        hit_bp = 0
            
        def bp_64(d, _):
            try:
                global hit_bp
                #print("Hit bp_64")
                ## Asserting the 64-bit registers (x0 to x31)
                ##self.assertTrue(d.x0 == 0x0000000000000000)  # x0 is always zero in RISC-V
                ##get all rpoperties x1,2,3 of d and print them (formatted in hex)
                #    
                #print("Registers: ")
                #for i in range(32):
                #    print(f"x{i}: {getattr(d, f'x{i}'):x}")
                #print("PC: ", hex(d.pc))
                #print("End of registers")
                self.assertTrue(d.x5 == 0x5566770011223344)#t0
                self.assertTrue(d.x6 == 0x6677001122334455)#t1
                self.assertTrue(d.x7 == 0x7700112233445566)#t2

                self.assertTrue(d.x9 == 0x0011223344556677)#s1
                self.assertTrue(d.x18 == 0x0011223344556677)#s2
                self.assertTrue(d.x19 == 0x1122334455667700)#s3
                self.assertTrue(d.x20 == 0x2233445566770011)#s4
                self.assertTrue(d.x21 == 0x3344556677001122)#s5
                self.assertTrue(d.x22 == 0x4455667700112233)#s6
                self.assertTrue(d.x23 == 0x5566770011223344)#s7
                self.assertTrue(d.x24 == 0x6677001122334455)#s8
                self.assertTrue(d.x25 == 0x7700112233445566)#s9
                self.assertTrue(d.x26 == 0x0011223344556677)#s10
                self.assertTrue(d.x27 == 0x1122334455667700)#s11
                self.assertTrue(d.x28 == 0x2233445566770011)#t3
                self.assertTrue(d.x29 == 0x3344556677001122)#t4
                self.assertTrue(d.x30 == 0x4455667700112233)#t5
                self.assertTrue(d.x31 == 0x5566770011223344)#t6

                self.assertTrue(d.pc == 0x106ba)
                self.assertTrue(d.t0 == 0x5566770011223344)
                self.assertTrue(d.t1 == 0x6677001122334455)
                self.assertTrue(d.t2 == 0x7700112233445566)
                self.assertTrue(d.s1 == 0x0011223344556677)
                self.assertTrue(d.s2 == 0x0011223344556677)
                self.assertTrue(d.s3 == 0x1122334455667700)
                self.assertTrue(d.s4 == 0x2233445566770011)
                self.assertTrue(d.s5 == 0x3344556677001122)
                self.assertTrue(d.s6 == 0x4455667700112233)
                self.assertTrue(d.s7 == 0x5566770011223344)
                self.assertTrue(d.s8 == 0x6677001122334455)
                self.assertTrue(d.s9 == 0x7700112233445566)
                self.assertTrue(d.s10 == 0x0011223344556677)
                self.assertTrue(d.s11 == 0x1122334455667700)
                self.assertTrue(d.t3 == 0x2233445566770011)
                self.assertTrue(d.t4 == 0x3344556677001122)
                self.assertTrue(d.t5 == 0x4455667700112233)
                self.assertTrue(d.t6 == 0x5566770011223344)
                

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
        # Set breakpoints with an offset of +432
        self.d.b(0x106ba, bp_64)  # Offset added for 64-bit register instructions
        self.d.cont()
        self.d.kill()

        self.assertTrue(hit_bp == 1)

        if self.exceptions:
            raise self.exceptions[0]

if __name__ == '__main__':
    unittest.main()
