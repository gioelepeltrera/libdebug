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

from libdebug import debugger
from pwn import *
import unittest
import logging
import re

logging.getLogger('pwnlib').setLevel(logging.ERROR)

class WatchpointBufferTest(unittest.TestCase):
    def setUp(self):
        self.exceptions = []
        self.write_hit = False
        self.write_count = 0
        self.read_hit = False
        self.read_count = 0
        self.read_write_hit = False
        self.read_write_count = 0
        self.buffer_addr = 0
        self.address = 0

    def test_buffer_watchpoints(self):
        def write_hook(d, b):
            try:
                #print("Write watchpoint hit!")
                self.write_hit = True
                self.write_count += 1
            except Exception as e:
                self.exceptions.append(e)

        def read_hook(d, b):
            try:
                #print("Read watchpoint hit!")
                self.read_hit = True
                self.read_count += 1
            except Exception as e:
                self.exceptions.append(e)
        def read_write_hook(d, b):
            try:
                #print("Read/Write watchpoint hit!")
                self.read_write_hit = True
                self.read_write_count += 1
            except Exception as e:
                self.exceptions.append(e)
        def hook(d,b):
            try:
                while self.address == 0:
                    sleep(0.1)
                d.b(self.address, write_hook, hardware_assisted=True, condition="W", length=8)
                d.b(self.address+0x30, read_write_hook, hardware_assisted=True, condition="RW", length=8) 
                d.b(self.address+0x60, read_hook, hardware_assisted=True, condition="R", length=4) 
        
                #print("Hook hit!")

                self.is_hit = True
            except Exception as e:
                self.exceptions.append(e)
        # Launch the C process
        r = process('arm_binaries/watchpoint_test')  # Replace with the actual binary name

        print("PID:", r.pid)
        # Create a debugger instance and attach to the process
        d = debugger()
        d.attach(r.pid)
        d.b("manipulate_buffer", hook, hardware_assisted=True)

        # Capture the address of the buffer from the C program's output
        output = r.recvuntil(b"program!\n")
        print("Program output:", output)
        d.cont()

        r.recvuntil(b'chars): ')
        r.sendline(b'Hello There!')
        addr = r.recvuntil(b'END\n')
        addr = addr.decode('utf-8')
        addr = re.findall(r'0x[0-9a-fA-F]+', addr)
        print("ADDRESS ",addr)
        self.address = int(addr[0], 16)
        d.kill()  # Kill the debugger after use

        print("Write count:", self.write_count)
        print("Read count:", self.read_count)
        print("Read/Write count:", self.read_write_count)

        # Assert that the watchpoints were triggered
        self.assertTrue(self.write_hit, "Write watchpoint was not hit")
        self.assertTrue(self.read_hit, "Read watchpoint was not hit")
        self.assertTrue(self.read_write_hit, "Read/Write watchpoint was not hit")
        self.assertEqual(self.write_count, 8, "Write watchpoint was not hit 8 times")
        self.assertEqual(self.read_count, 4, "Read watchpoint was not hit 4 times")
        self.assertEqual(self.read_write_count, 16, "Read/Write watchpoint was not hit 16 times")

        # Raise any exceptions encountered during the test
        if self.exceptions:
            raise self.exceptions[0]

if __name__ == '__main__':
    unittest.main()

