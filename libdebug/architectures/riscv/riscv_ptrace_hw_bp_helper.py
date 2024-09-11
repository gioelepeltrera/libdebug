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

from libdebug.architectures.ptrace_hardware_breakpoint_manager import (
    PtraceHardwareBreakpointManager,
)
from libdebug.data.breakpoint import Breakpoint
from libdebug.liblog import liblog

class RiscvPtraceHardwareBreakpointManager(PtraceHardwareBreakpointManager):
    """A hardware breakpoint manager for the ARM architecture.

    Attributes:
        getregset (callable): A function that reads a register set from the target process.
        setregset (callable): A function that writes a register set to the target process.
        breakpoint_count (int): The number of hardware breakpoints set.
    """


    def __init__(self, getregset, setregset):
        super().__init__(getregset=getregset, setregset=setregset)

    def install_breakpoint(self, bp: Breakpoint):
        pass

    def remove_breakpoint(self, bp: Breakpoint):
        pass
    def available_breakpoints(self) -> int:
        pass
    