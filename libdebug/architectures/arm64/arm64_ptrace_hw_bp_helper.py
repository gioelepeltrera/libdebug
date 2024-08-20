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


# Define the offsets and control bits for ARM debug registers
ARM_DBGREGS_OFF = {
    "BVR0": 0x0880,  # Breakpoint Value Register
    "BVR1": 0x0884,
    "BVR2": 0x0888,
    "BVR3": 0x088C,
    # Add more if ARM supports more registers
}

ARM_DBGREGS_CTRL_LOCAL = {"BVR0": 0x1, "BVR1": 0x2, "BVR2": 0x4, "BVR3": 0x8}
ARM_DBGREGS_CTRL_COND = {"BVR0": 0x4, "BVR1": 0x8, "BVR2": 0x10, "BVR3": 0x20}
ARM_DBGREGS_CTRL_COND_VAL = {"X": 0, "W": 2, "RW": 1}  # ARM conditions
ARM_DBGREGS_CTRL_LEN = {"BVR0": 0x2, "BVR1": 0x4, "BVR2": 0x8, "BVR3": 0x10}
ARM_DBGREGS_CTRL_LEN_VAL = {1: 0, 2: 1, 4: 3}  # ARM lengths (byte, halfword, word)

ARM_DBREGS_COUNT = 4  # Adjust according to the specific ARM implementation


class Arm64PtraceHardwareBreakpointManager(PtraceHardwareBreakpointManager):
    """A hardware breakpoint manager for the ARM architecture.

    Attributes:
        peek_mem (callable): A function that reads a number of bytes from the target process memory.
        poke_mem (callable): A function that writes a number of bytes to the target process memory.
        breakpoint_count (int): The number of hardware breakpoints set.
    """


    def __init__(self, peek_mem, poke_mem):
        super().__init__(peek_mem, poke_mem)
        self.breakpoint_registers = {
            "BVR0": None,
            "BVR1": None,
            "BVR2": None,
            "BVR3": None,
        }

    def install_breakpoint(self, bp: Breakpoint):
        """Installs a hardware breakpoint at the provided location."""
        if self.breakpoint_count >= ARM_DBREGS_COUNT:
            raise RuntimeError("No more hardware breakpoints available.")

        # Find the first available breakpoint register
        register = next(
            reg for reg, bp in self.breakpoint_registers.items() if bp is None
        )
        liblog.debugger(f"Installing hardware breakpoint on register {register}.")

        # Write the breakpoint address in the register
        self.poke_mem(ARM_DBGREGS_OFF[register], bp.address)

        # Set the breakpoint control register
        ctrl = (
            ARM_DBGREGS_CTRL_LOCAL[register]
            | (
                ARM_DBGREGS_CTRL_COND_VAL[bp.condition]
                << ARM_DBGREGS_CTRL_COND[register]
            )
            | (
                ARM_DBGREGS_CTRL_LEN_VAL[bp.length]
                << ARM_DBGREGS_CTRL_LEN[register]
            )
        )

        # Read the current value of the DBGDSCR register (ARM Debug Status and Control Register)
        current_ctrl = self.peek_mem(ARM_DBGREGS_OFF["DBGDSCR"])

        # Clear condition and length fields for the current register
        current_ctrl &= ~(0x3 << ARM_DBGREGS_CTRL_COND[register])
        current_ctrl &= ~(0x3 << ARM_DBGREGS_CTRL_LEN[register])

        # Set the new value of the register
        current_ctrl |= ctrl

        # Write the new value of the DBGDSCR register
        self.poke_mem(ARM_DBGREGS_OFF["DBGDSCR"], current_ctrl)

        # Save the breakpoint
        self.breakpoint_registers[register] = bp

        liblog.debugger(f"Hardware breakpoint installed on register {register}.")

        self.breakpoint_count += 1

    def remove_breakpoint(self, bp: Breakpoint):
        """Removes a hardware breakpoint at the provided location."""
        if self.breakpoint_count <= 0:
            raise RuntimeError("No more hardware breakpoints to remove.")

        # Find the breakpoint register
        register = next(
            reg for reg, bp_ in self.breakpoint_registers.items() if bp_ == bp
        )

        if register is None:
            raise RuntimeError("Hardware breakpoint not found.")

        liblog.debugger(f"Removing hardware breakpoint on register {register}.")

        # Clear the breakpoint address in the register
        self.poke_mem(ARM_DBGREGS_OFF[register], 0)

        # Read the current value of the control register
        current_ctrl = self.peek_mem(ARM_DBGREGS_OFF["DBGDSCR"])

        # Clear the breakpoint control register
        current_ctrl &= ~ARM_DBGREGS_CTRL_LOCAL[register]

        # Write the new value of the DBGDSCR register
        self.poke_mem(ARM_DBGREGS_OFF["DBGDSCR"], current_ctrl)

        # Remove the breakpoint
        self.breakpoint_registers[register] = None

        liblog.debugger(f"Hardware breakpoint removed from register {register}.")

        self.breakpoint_count -= 1

    def available_breakpoints(self) -> int:
        """Returns the number of available hardware breakpoint registers."""
        return ARM_DBREGS_COUNT - self.breakpoint_count