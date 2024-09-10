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
from libdebug.cffi._ptrace_cffi import ffi
from libdebug.utils.arm_constants import *

class Arm64PtraceHardwareBreakpointManager(PtraceHardwareBreakpointManager):
    """A hardware breakpoint manager for the ARM architecture.

    Attributes:
        getregset (callable): A function that reads a register set from the target process.
        setregset (callable): A function that writes a register set to the target process.
        breakpoint_count (int): The number of hardware breakpoints set.
    """


    def __init__(self, getregset, setregset):
        super().__init__(getregset=getregset, setregset=setregset)
        self.breakpoint_registers = {
            "HWBPREG_0": None,
            "HWBPREG_1": None,
            "HWBPREG_2": None,
            "HWBPREG_3": None,
            "HWBPREG_4": None,
            "HWBPREG_5": None,
        }
        self.watchpoint_registers = {
            "HWWPREG_0": None,
            "HWWPREG_1": None,
            "HWWPREG_2": None,
            "HWWPREG_3": None,
        }

    def install_breakpoint(self, bp: Breakpoint):
        """Installs a hardware breakpoint at the provided location."""
        if bp.condition == "X":
            if self.breakpoint_count >= ARM_DBREGS_COUNT:
                raise RuntimeError("No more hardware breakpoints available.")
        else:
            if self.watchpoint_count >= ARM_WATCHDB_COUNT:
                raise RuntimeError("No more hardware watchpoints available.")

        hw_dbg_state = ffi.new("struct user_hwdebug_state *")

        if bp.condition == "X":
            self.getregset(NT_ARM_HW_BREAK, hw_dbg_state, USER_HWDEBUG_STATE_LEN)
        else:
            self.getregset(NT_ARM_HW_WATCH, hw_dbg_state, USER_WATCH_STATE_LEN)
        free = -1 
        
        for i in range(ARM_DBREGS_COUNT if bp.condition=="X" else ARM_WATCHDB_COUNT):
            if free <0 and hw_dbg_state.dbg_regs[i].ctrl & 1 == 0:
                free = i
        
        if bp.condition == "X" :
            if free < 0:
                raise RuntimeError("No more hardware breakpoints available.")
            else:
                liblog.debugger(f"Trying to install hardware breakpoint on register {free}.")
        else:
            if free < 0:
                raise RuntimeError("No more hardware watchpoints available.")
            else:
                liblog.debugger(f"Trying to install hardware watchpoint on register {free}.")

        # Write the breakpoint address in the register
        hw_dbg_state.dbg_regs[free].addr = bp.address
        enabled = 1
        ctrl =  (ARM_DBGREGS_CTRL_LEN_VAL[bp.length] << 5) |\
                (ARM_DBGREGS_CTRL_COND_VAL[bp.condition] << 3) | \
                (ARM_DBREGS_PRIV_LEVEL_VAL["EL0"] << 1) | enabled
        hw_dbg_state.dbg_regs[free].ctrl = ctrl

        if bp.condition == "X":
            self.setregset(NT_ARM_HW_BREAK, hw_dbg_state, USER_HWDEBUG_STATE_LEN)
        else:
            self.setregset(NT_ARM_HW_WATCH, hw_dbg_state, USER_WATCH_STATE_LEN)

        if bp.condition == "X":
            self.getregset(NT_ARM_HW_BREAK, hw_dbg_state, USER_HWDEBUG_STATE_LEN)
        else:
            self.getregset(NT_ARM_HW_WATCH, hw_dbg_state, USER_WATCH_STATE_LEN)
        
        if bp.condition == "X":    
            self.breakpoint_registers[free] = bp
            liblog.debugger(f"Hardware breakpoint installed on register {free}.")
            self.breakpoint_count += 1
        else:
            self.watchpoint_registers[free] = bp
            liblog.debugger(f"Hardware watchpoint installed on register {free}.")
            self.watchpoint_count += 1

        self.getregset(NT_ARM_HW_BREAK if bp.condition == "X" else NT_ARM_HW_WATCH, hw_dbg_state, USER_HWDEBUG_STATE_LEN if bp.condition == "X" else USER_WATCH_STATE_LEN)
        
        print("____BP _DEBUG_After setting the register___")
        for i in range(ARM_DBREGS_COUNT if bp.condition == "X" else ARM_WATCHDB_COUNT):
            print(f"{i} -- 0x{hw_dbg_state.dbg_regs[i].addr:x} -- ctrl: 0x{hw_dbg_state.dbg_regs[i].ctrl:x}")

    

    def remove_breakpoint(self, bp: Breakpoint):
        """Removes a hardware breakpoint at the provided location."""
        if self.breakpoint_count <= 0:
            raise RuntimeError("No more hardware breakpoints to remove.")

        hw_dbg_state = ffi.new("struct user_hwdebug_state *")

        if bp.condition == "X":
            self.getregset(NT_ARM_HW_BREAK, hw_dbg_state, USER_HWDEBUG_STATE_LEN)
        else:
            self.getregset(NT_ARM_HW_WATCH, hw_dbg_state, USER_WATCH_STATE_LEN)
        free = -1 

        for i in range(ARM_DBREGS_COUNT if bp.condition=="X" else ARM_WATCHDB_COUNT):
            if hw_dbg_state.dbg_regs[i].addr == bp.address:
                free = i
        
        if bp.condition == "X":
            if free < 0:
                raise RuntimeError("No hardware breakpoint to remove.")
            else:
                liblog.debugger(f"Trying to remove hardware breakpoint on register {free}.")
        else:
            if free < 0:
                raise RuntimeError("No hardware watchpoint to remove.")
            else:
                liblog.debugger(f"Trying to remove hardware watchpoint on register {free}.")
        
        # Write the breakpoint address in the register
        hw_dbg_state.dbg_regs[free].addr = 0
        hw_dbg_state.dbg_regs[free].ctrl = 0

        if bp.condition == "X":
            self.setregset(NT_ARM_HW_BREAK, hw_dbg_state, USER_HWDEBUG_STATE_LEN)
        else:
            self.setregset(NT_ARM_HW_WATCH, hw_dbg_state, USER_WATCH_STATE_LEN)

        if bp.condition == "X":
            self.breakpoint_registers[free] = None
            liblog.debugger(f"Hardware breakpoint removed from register {free}.")
            self.breakpoint_count -= 1
        else:
            self.watchpoint_registers[free] = None
            liblog.debugger(f"Hardware watchpoint removed from register {free}.")
            self.watchpoint_count -= 1

    def available_breakpoints(self) -> int:
        """Returns the number of available hardware breakpoint registers."""
        return ARM_DBREGS_COUNT - self.breakpoint_count
    
    def available_watchpoints(self) -> int:
        """Returns the number of available hardware breakpoint registers."""
        return ARM_WATCHDB_COUNT - self.watchpoint_count