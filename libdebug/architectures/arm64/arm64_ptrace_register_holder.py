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
    get_reg_32,
    set_reg_64,
    set_reg_32,
)

# ARM64 General-Purpose Registers
ARM64_GP_REGS = list(range(0, 31))

# ARM64 Special Registers
ARM64_SPECIAL_REGS = ["sp","pc","pstate"]

# List of all ARM64 Registers (order matters as it should match the order in the register file)
ARM64_REGS = ARM64_GP_REGS + ARM64_SPECIAL_REGS


@dataclass
class Arm64PtraceRegisterHolder(PtraceRegisterHolder):
    """A class that provides views and setters for the registers of an ARM64 process, specifically for the `ptrace` debugging backend."""

    def apply_on(self, target, target_class):
        target.regs = {}

        for i, name in enumerate(ARM64_REGS):
            if isinstance(name, int):  # General-purpose registers are indexed by numbers
                target.regs[name] = u64(self.register_file[i * 8 : (i + 1) * 8])
            else:  # Special registers
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

        def get_property_32(name):
            def getter(self):
                if self.running:
                    raise RuntimeError(
                        "Cannot access registers while the process is running."
                    )
                return get_reg_32(self.regs, name)

            def setter(self, value):
                if self.running:
                    raise RuntimeError(
                        "Cannot access registers while the process is running."
                    )
                set_reg_32(self.regs, name, value)

            return property(getter, setter, None, name)

        # Setup accessors for general-purpose registers
        for index in ARM64_GP_REGS:
            setattr(target_class, f"x{index}", get_property_64(index))
            setattr(target_class, f"w{index}", get_property_32(index))

        # Setup accessor for special registers (sp, pc, etc.)
        for name in ARM64_SPECIAL_REGS:
            setattr(target_class, name, get_property_64(name))
        
        # Provide `rip` compatibility for AArch64 by mapping it to `pc`s
        setattr(target_class, "rip", get_property_64("pc"))#general instruction_pointer
        setattr(target_class, "rsp", get_property_64("sp"))#general stack_pointer

    def flush(self, source):
        """Flushes the register values to the target process."""
        buffer = b""
        for name in ARM64_REGS:
            buffer += p64(source.regs[name])
        self.ptrace_setter(buffer)