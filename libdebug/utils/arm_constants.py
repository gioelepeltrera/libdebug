# 
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2024 Roberto Gioele Peltrera.
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


'''
CONTROL REGISTER:
Bit 0: Enable bit
Bit 1-2: Privilege level
Bit 3-4: Condition
Bit 5-13: Length
'''

ARM_DBREGS_PRIV_LEVEL_VAL = {"EL0": 0, "EL1": 1, "EL2": 2, "EL3": 3}#EL0 is user mode, EL1 is kernel mode, EL2 is hypervisor mode, EL3 is secure monitor mode
ARM_DBGREGS_CTRL_COND_VAL = {"X": 0, "R":1 ,"W": 2, "RW": 3}
ARM_DBGREGS_CTRL_LEN_VAL = {1:1, 2:3, 3:7, 4:15, 5:31, 6:63, 7:127, 8:511} #ARM lengths (1 byte, 2 bytes, 3 bytes, 4 bytes, 5 bytes, 6 bytes, 7 bytes, 8 bytes)

ARM_BRK_INSTRUCTION = 0xd4200000

NT_ARM_HW_BREAK = 0x402
NT_ARM_HW_WATCH = 0x403


ARM_DBREGS_COUNT = 6  # Adjust according to the specific ARM implementation
ARM_WATCHDB_COUNT = 4 # Adjust according to the specific ARM implementation
USER_HWDEBUG_STATE_LEN = 0x68 # Adjust according to the specific ARM implementation
USER_WATCH_STATE_LEN = 0x48 # Adjust according to the specific ARM implementation