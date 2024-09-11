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

        # Setup accessor for the program counter (pc)
        setattr(target_class, "pc", get_property_64("pc"))
        setattr(target_class, "rip", get_property_64("pc"))
        setattr(target_class, "ra", get_property_64(1))

        # Define the stack pointer (sp) as an alias for x2
        setattr(target_class, "rsp", get_property_64(2))

    def flush(self, source):
        """Flushes the register values to the target process."""
        buffer = b""
        for name in RISCV_REGS:
            buffer += p64(source.regs[name])
        self.ptrace_setter(buffer)
