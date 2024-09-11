#
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2023 Roberto Alessandro Bertolini, Gioele Peltrera.
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
from libdebug.architectures.amd64.amd64_ptrace_hw_bp_helper import (
    Amd64PtraceHardwareBreakpointManager,
)
from libdebug.architectures.arm64.arm64_ptrace_hw_bp_helper import (
    Arm64PtraceHardwareBreakpointManager,
)
from libdebug.architectures.riscv.riscv_ptrace_hw_bp_helper import (
    RiscvPtraceHardwareBreakpointManager,
)
from typing import Callable
import platform

def ptrace_hardware_breakpoint_manager_provider(
    peek_mem: Callable[[int], int] = None,
    poke_mem: Callable[[int, int], None] = None,
#    def _getregset(self, type: int, regset: "ctype", size: int):
    getregset: Callable[[int, "ctype", int], int] = None,
    setregset: Callable[[int, "ctype", int], int] = None,
    architecture: str = platform.machine(),
) -> PtraceHardwareBreakpointManager:
    """Returns an instance of the hardware breakpoint manager to be used by the `Debugger` class."""
    architecture = platform.machine()
    
    match architecture:
        case "x86_64":
            return Amd64PtraceHardwareBreakpointManager(peek_mem, poke_mem)
        case "aarch64":
            return Arm64PtraceHardwareBreakpointManager(getregset, setregset)
        case "riscv64":
            return RiscvPtraceHardwareBreakpointManager(getregset, setregset)
        case _:
            raise NotImplementedError(f"Architecture {architecture} not available.")
