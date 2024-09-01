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
from libdebug.cffi._ptrace_cffi import ffi, lib

# Define the offsets and control bits for ARM debug registers
ARM_DBGREGS_OFF = {
    "BVR0": 0x100,  # Breakpoint Value Register 0
    "BVR1": 0x104,  # Breakpoint Value Register 1
    "BVR2": 0x108,  # Breakpoint Value Register 2
    "BVR3": 0x10C,  # Breakpoint Value Register 3
    # Add more if needed
}

ARM_DBGREGS_CTRL_LOCAL = {"BVR0": 0x1, "BVR1": 0x2, "BVR2": 0x4, "BVR3": 0x8}
ARM_DBGREGS_CTRL_COND = {"BVR0": 0x4, "BVR1": 0x8, "BVR2": 0x10, "BVR3": 0x20}
ARM_DBGREGS_CTRL_COND_VAL = {"X": 0, "W": 2, "RW": 1}  # ARM conditions
ARM_DBGREGS_CTRL_LEN = {"BVR0": 0x2, "BVR1": 0x4, "BVR2": 0x8, "BVR3": 0x10}
ARM_DBGREGS_CTRL_LEN_VAL = {1: 0, 2: 1, 4: 3}  # ARM lengths (byte, halfword, word)

ARM_DBREGS_COUNT = 6  # Adjust according to the specific ARM implementation

NT_ARM_HW_BREAK = 0x402

class Arm64PtraceHardwareBreakpointManager(PtraceHardwareBreakpointManager):
    """A hardware breakpoint manager for the ARM architecture.

    Attributes:
        getregset (callable): A function that reads a register set from the target process.
        setregset (callable): A function that writes a register set to the target process.
        breakpoint_count (int): The number of hardware breakpoints set.
    """


    def __init__(self, getregset, setregset):
        super().__init__(getregset, setregset)
        self.breakpoint_registers = {
            "HWBPREG_0": None,
            "HWBPREG_1": None,
            "HWBPREG_2": None,
            "HWBPREG_3": None,
            "HWBPREG_4": None,
            "HWBPREG_5": None,
        }

    def install_breakpoint(self, bp: Breakpoint):
        """Installs a hardware breakpoint at the provided location."""
        if self.breakpoint_count >= ARM_DBREGS_COUNT:
            raise RuntimeError("No more hardware breakpoints available.")

        hw_dbg_state = ffi.new("struct user_hwdebug_state *")
        res = self.getregset(NT_ARM_HW_BREAK, hw_dbg_state, ffi.sizeof(hw_dbg_state))
        if res < 0:
            raise RuntimeError("Failed to read the hardware debug state.")
        free = -1 
        print("____BP _DEBUG_Before setting the register___")

        for i in range(ARM_DBREGS_COUNT):
            print(str(i)+" -- "+hw_dbg_state.dbg_regs[i].addr+"  -- ctrl: "+hw_dbg_state.dbg_regs[i].ctrl)
            if free <1 and hw_dbg_state.dbg_regs[i].ctrl & 1 == 0:
                free = i
        
        if free < 0:
            raise RuntimeError("No more hardware breakpoints available.")
        else:
            liblog.debugger(f"Trying to install hardware breakpoint on register {free}.")

        # Write the breakpoint address in the register
        hw_dbg_state.dbg_regs[free].addr = bp.address
        hw_dbg_state.dbg_regs[free].ctrl = 0x25#TODO set better

        res = self.setregset(NT_ARM_HW_BREAK, hw_dbg_state, ffi.sizeof(hw_dbg_state))
        if res < 0:
            raise RuntimeError("Failed to write the hardware debug state.")
        else:
            #print all the registers
            res = self.getregset(NT_ARM_HW_BREAK, hw_dbg_state, ffi.sizeof(hw_dbg_state))
            print("____BP _DEBUG_After setting the register___")
            for i in range(ARM_DBREGS_COUNT):
                print(str(i)+" -- "+hw_dbg_state.dbg_regs[i].addr+"  -- ctrl: "+hw_dbg_state.dbg_regs[i].ctrl)

    
      
        # Save the breakpoint
        self.breakpoint_registers[free] = bp

        liblog.debugger(f"Hardware breakpoint installed on register {free}.")

        self.breakpoint_count += 1

    def remove_breakpoint(self, bp: Breakpoint):
        """Removes a hardware breakpoint at the provided location."""
        if self.breakpoint_count <= 0:
            raise RuntimeError("No more hardware breakpoints to remove.")

        hw_dbg_state = ffi.new("struct user_hwdebug_state *")
        res = self.getregset(NT_ARM_HW_BREAK, hw_dbg_state, ffi.sizeof(hw_dbg_state))
        if res < 0:
            raise RuntimeError("Failed to read the hardware debug state.")
        free = -1 
        print("____BP _DEBUG_Before nullifying the register___")

        for i in range(ARM_DBREGS_COUNT):
            if hw_dbg_state.dbg_regs[i].addr == bp.address:
                free = i
        
        if free < 0:
            raise RuntimeError("No hardware breakpoint to remove.")
        else:
            liblog.debugger(f"Trying to remove hardware breakpoint on register {free}.")

        # Write the breakpoint address in the register
        hw_dbg_state.dbg_regs[free].addr = 0
        hw_dbg_state.dbg_regs[free].ctrl = 0

        res = self.setregset(NT_ARM_HW_BREAK, hw_dbg_state, ffi.sizeof(hw_dbg_state))
        if res < 0:
            raise RuntimeError("Failed to write the hardware debug state.")
        else:
            #print all the registers
            res = self.getregset(NT_ARM_HW_BREAK, hw_dbg_state, ffi.sizeof(hw_dbg_state))
            print("____BP _DEBUG_After setting the register___")
            for i in range(ARM_DBREGS_COUNT):
                print(str(i)+" -- "+hw_dbg_state.dbg_regs[i].addr+"  -- ctrl: "+hw_dbg_state.dbg_regs[i].ctrl)

    
        # Remove the breakpoint
        self.breakpoint_registers[free] = None

        liblog.debugger(f"Hardware breakpoint removed from register {free}.")

        self.breakpoint_count -= 1

    def available_breakpoints(self) -> int:
        """Returns the number of available hardware breakpoint registers."""
        return ARM_DBREGS_COUNT - self.breakpoint_count