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

class RiscVStackUnwinding:
    """
    Class that provides stack unwinding for the RISC-V architecture.
    """

    def unwind(self, target: "Debugger") -> list:
        """
        Unwind the stack of a process using both the frame pointer (s0) and the stack pointer (sp).

        Args:
            target (Debugger): The target Debugger.

        Returns:
            list: A list of return addresses (stack trace).
        """

        # Initialize stack trace with the current program counter (PC)
        stack_trace = [target.pc]
        current_ra = target.ra if target.ra else None
        current_fp = target.x8  # Frame pointer (s0/x8)
        current_sp = target.sp  # Stack pointer (sp)

        print(f"Starting unwinding:\nPC: {target.pc:x}, FP (s0/x8): {current_fp:x}, SP: {current_sp:x}, RA: {current_ra:x}")

        # Attempt stack unwinding using the frame pointer (s0/x8)
        while current_fp:
            try:
                # Read the return address from the current frame (FP + 8)
                ra = int.from_bytes(target.memory[current_fp + 8, 8], byteorder="little")
                next_fp = int.from_bytes(target.memory[current_fp, 8], byteorder="little")

                # Append return address to stack trace
                stack_trace.append(ra)
                print(f"Unwound function: RA={ra:x}, FP={current_fp:x}, Next FP={next_fp:x}")

                # Move to the next frame
                current_fp = next_fp

            except OSError:
                print("Error reading memory at FP; manual stack scanning will be attempted.")
                break

        # If frame-pointer-based unwinding failed, manually scan the stack for return addresses
        print("\nManual stack scanning for return addresses:")
        if current_ra and current_ra not in stack_trace:
            stack_trace.append(current_ra)

        # Perform manual scanning through the stack memory
        while current_sp:
            try:
                # Scan the stack at offsets from the current SP
                for offset in range(0, 128, 8):
                    potential_ra = int.from_bytes(target.memory[current_sp + offset, 8], byteorder="little")

                    # Append potential return addresses found in the stack
                    stack_trace.append(potential_ra)
                    print(f"Potential return address found at (sp + {offset}): {potential_ra:x}")

                # Move to the next block of stack memory
                current_sp += 128  # Adjust step size as needed

            except OSError:
                print("Error reading memory while scanning the stack.")
                break

        # Return the complete stack trace
        return stack_trace
