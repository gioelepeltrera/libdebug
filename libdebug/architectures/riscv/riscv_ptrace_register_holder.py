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

from dataclasses import dataclass
from libdebug.architectures.register_holder import PtraceRegisterHolder
from libdebug.utils.packing_utils import u64, p64
from libdebug.utils.register_utils import (
    get_reg_64,
    set_reg_64,
)

# Define RISC-V General-Purpose Registers (x0 to x31)
RISCV_GP_REGS = list(range(0, 32))

# Define the RISC-V Program Counter (pc) register
RISCV_SPECIAL_REGS = ["pc"]

# List of all RISC-V Registers (order matters as it should match the order in the register file)
RISCV_REGS = RISCV_GP_REGS + RISCV_SPECIAL_REGS


@dataclass
class RiscVPtraceRegisterHolder(PtraceRegisterHolder):
    """A class that provides views and setters for the registers of a RISC-V process, specifically for the `ptrace` debugging backend."""

    def apply_on(self, target, target_class):
        target.regs = {}

        # Load general-purpose and special registers into target's register dictionary
        for i, name in enumerate(RISCV_REGS):
            target.regs[name] = u64(self.register_file[i * 8 : (i + 1) * 8])

        def get_property_64(name):
            def getter(self):
                if self.running:
                    raise RuntimeError(
                        "Cannot access registers while the process is running."
                    )
                return get_reg_64(self.regs, name)

            def setter(self, value):
                if self.running:
                    raise RuntimeError(
                        "Cannot access registers while the process is running."
                    )
                set_reg_64(self.regs, name, value)

            return property(getter, setter, None, name)

        # Setup accessors for general-purpose registers x0 to x31
        for index in RISCV_GP_REGS:
            setattr(target_class, f"x{index}", get_property_64(index))

        setattr(target_class, "rip", get_property_64("pc"))
        setattr(target_class, "rsp", get_property_64(2))

        # Setup accessor for the program counter (pc)
        setattr(target_class, "pc", get_property_64("pc"))
        
        setattr(target_class, "ra", get_property_64(1))
        setattr(target_class, "sp", get_property_64(2))

        setattr(target_class, "gp", get_property_64(3))
        setattr(target_class, "tp", get_property_64(4))
        
        setattr(target_class, "s0", get_property_64(8))
        setattr(target_class, "fp", get_property_64(8))
        setattr(target_class, "s1", get_property_64(9))


        # Define properties for the specific ABI names
        setattr(target_class, "t0", get_property_64(5))  # t0 maps to x5
        setattr(target_class, "t1", get_property_64(6))  # t1 maps to x6
        setattr(target_class, "t2", get_property_64(7))  # t2 maps to x7
        setattr(target_class, "t3", get_property_64(28)) # t3 maps to x28
        setattr(target_class, "t4", get_property_64(29)) # t4 maps to x29
        setattr(target_class, "t5", get_property_64(30)) # t5 maps to x30
        setattr(target_class, "t6", get_property_64(31)) # t6 maps to x31

        setattr(target_class, "s0", get_property_64(8))  # s0 maps to x8
        setattr(target_class, "s1", get_property_64(9))  # s1 maps to x9
        setattr(target_class, "s2", get_property_64(18)) # s2 maps to x18
        setattr(target_class, "s3", get_property_64(19)) # s3 maps to x19
        setattr(target_class, "s4", get_property_64(20)) # s4 maps to x20
        setattr(target_class, "s5", get_property_64(21)) # s5 maps to x21
        setattr(target_class, "s6", get_property_64(22)) # s6 maps to x22
        setattr(target_class, "s7", get_property_64(23)) # s7 maps to x23
        setattr(target_class, "s8", get_property_64(24)) # s8 maps to x24
        setattr(target_class, "s9", get_property_64(25)) # s9 maps to x25
        setattr(target_class, "s10", get_property_64(26))# s10 maps to x26
        setattr(target_class, "s11", get_property_64(27))# s11 maps to x27

        # Define properties for function arguments and return values
        setattr(target_class, "a0", get_property_64(10))  # a0 maps to x10
        setattr(target_class, "a1", get_property_64(11))  # a1 maps to x11
        setattr(target_class, "a2", get_property_64(12))  # a2 maps to x12
        setattr(target_class, "a3", get_property_64(13))  # a3 maps to x13
        setattr(target_class, "a4", get_property_64(14))  # a4 maps to x14
        setattr(target_class, "a5", get_property_64(15))  # a5 maps to x15
        setattr(target_class, "a6", get_property_64(16))  # a6 maps to x16
        setattr(target_class, "a7", get_property_64(17))  # a7 maps to x17



    def flush(self, source):
        """Flushes the register values to the target process."""
        buffer = b""
        for name in RISCV_REGS:
            buffer += p64(source.regs[name])
        self.ptrace_setter(buffer)
