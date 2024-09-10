#
# This file is part of libdebug Python library (https://github.com/gioelepeltrera/libdebug).
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

from libdebug import debugger
from pwn import *
import unittest
import logging

logging.getLogger('pwnlib').setLevel(logging.ERROR)

class AttachTest(unittest.TestCase):
    def setUp(self):
        self.exceptions = []
        self.is_hit = False

    def test_attach(self):
        
        def hook(d,b):
            try:
                self.is_hit = True
            except Exception as e:
                self.exceptions.append(e)
        
        r = process('arm_binaries/attach_test')

        d = debugger()
        d.attach(r.pid)
        d.b('printName', hook, hardware_assisted=True)
        d.cont()

        r.recvuntil(b'name:')
        r.sendline(b'Io_gioele')

        d.kill()
        
        self.assertTrue(self.is_hit)
        if self.exceptions:
            raise self.exceptions[0]