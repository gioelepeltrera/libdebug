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

class RiscVStackUnwinding():
    """
    Class that provides stack unwinding for the RISC-V architecture.
    """

    def unwind(self, target: "Debugger") -> list:
        """
        Unwind the stack of a process using both the frame pointer (s0/x8) and the stack pointer (sp/x2).

        Args:
            target (Debugger): The target Debugger.

        Returns:
            list: A list of return addresses (stack trace).
        """

        # Start with the current program counter (pc)
        stack_trace = [target.pc]
        ra = target.ra if target.ra else None  # Use return address if available

        # Frame pointer-based unwinding
        current_fp = target.x8  # Frame pointer (s0)
        temp_stack_fp = []

        print("\nStack Unwinding via Frame Pointer (s0/x8):")

        # Keep unwinding until we reach the end or invalid frame
        while current_fp:
            try:
                # Print debugging information about current frame pointer
                print(f"Current FP: {current_fp:x}")

                # Read the return address from the stack frame (fp + 8 contains ra)
                return_address = int.from_bytes(target.memory[current_fp + 8, 8], byteorder="little")
                print(f"Return Address: {return_address:x}")

                # Append the return address to the temporary stack
                temp_stack_fp.append(return_address)

                # Read the next frame pointer (fp contains the previous frame's fp)
                next_fp = int.from_bytes(target.memory[current_fp, 8], byteorder="little")
                print(f"Next FP: {next_fp:x}")

                # Print additional stack values (optional, for debugging)
                for offset in range(16, 64, 8):
                    value_at_offset = int.from_bytes(target.memory[current_fp + offset, 8], byteorder="little")
                    print(f"Value at (fp + {offset}): {value_at_offset:x}")

                # Move to the next frame
                current_fp = next_fp

            except OSError:
                print("Error reading memory while unwinding stack.")
                break

        # Add the return address from the link register (ra) if not already in the stack trace
        if ra not in temp_stack_fp:
            stack_trace += [ra] + temp_stack_fp
        else:
            stack_trace += temp_stack_fp

        # Return the full stack trace
        return stack_trace
