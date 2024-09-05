#
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2023 Roberto Alessandro Bertolini, Gabriele Digregorio.
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

import errno
from libdebug.utils.pipe_manager import PipeManager
from libdebug.interfaces.debugging_interface import DebuggingInterface
from libdebug.architectures.register_helper import register_holder_provider
from libdebug.architectures.register_holder import RegisterHolder
from libdebug.architectures.ptrace_hardware_breakpoint_provider import (
    ptrace_hardware_breakpoint_manager_provider,
)
from libdebug.cffi import _ptrace_cffi
from libdebug.data.breakpoint import Breakpoint
from libdebug.data.memory_view import MemoryView
from libdebug.utils.elf_utils import is_pie
from libdebug.utils.debugging_utils import normalize_and_validate_address
from libdebug.utils.process_utils import (
    get_process_maps,
    get_open_fds,
    guess_base_address,
    invalidate_process_cache,
    disable_self_aslr,
)
from libdebug.liblog import liblog
import os
import signal
import pty
import tty
import platform

NT_PRSTATUS = 1 


class PtraceInterface(DebuggingInterface):
    """The interface used by `Debugger` to communicate with the `ptrace` debugging backend."""

    def __init__(self):
        self.lib_trace = _ptrace_cffi.lib
        self.ffi = _ptrace_cffi.ffi

        # The PID of the process being traced
        self.process_id = None
        self.software_breakpoints = {}
        self.hardware_bp_helper = None

    def _set_options(self):
        """Sets the tracer options."""
        self.lib_trace.ptrace_set_options(self.process_id)

    def _trace_self(self):
        """Traces the current process."""
        result = self.lib_trace.ptrace_trace_me()
        # TODO: investigate errno handling
        if result == -1:
            errno_val = self.ffi.errno
            raise OSError(errno_val, errno.errorcode[errno_val])

    def run(self, argv: str | list[str], enable_aslr: bool, env: dict[str, str] = None) -> int:
        """Runs the specified process.

        Args:
            argv (str | list[str]): The command line to execute.
            enable_aslr (bool): Whether to enable ASLR or not.
            env (dict[str, str], optional): The environment variables to use. Defaults to None.
            
        Returns:
            int: The PID of the process.
        """

        liblog.debugger("Running %s", argv)

        # Creating pipes for stdin, stdout, stderr
        self.stdin_read, self.stdin_write = os.pipe()
        self.stdout_read, self.stdout_write = pty.openpty()
        self.stderr_read, self.stderr_write = pty.openpty()

        # Setting stdout, stderr to raw mode to avoid terminal control codes interfering with the 
        # output
        tty.setraw(self.stdout_read)
        tty.setraw(self.stdout_write)
        tty.setraw(self.stderr_read)
        tty.setraw(self.stderr_write)

        child_pid = os.fork()
        if child_pid == 0:
            self._setup_child(argv, enable_aslr, env)
            assert False
        else:
            self.process_id = child_pid
            self._setup_parent()
            return self._setup_pipe()

    def _setup_child(self, argv, enable_aslr, env):
        self._trace_self()

        try:
            # Close the write end for stdin and the read ends for stdout and stderr
            # in the child process since it is going to read from stdin and write to
            # stdout and stderr
            os.close(self.stdin_write)
            os.close(self.stdout_read)
            os.close(self.stderr_read)

            # Redirect stdin, stdout, and stderr of child process
            os.dup2(self.stdin_read, 0)
            os.dup2(self.stdout_write, 1)
            os.dup2(self.stderr_write, 2)

            # Close the original fds in the child process since now they are duplicated
            # by 0, 1, and 2 (they point to the same location)
            os.close(self.stdin_read)
            os.close(self.stdout_write)
            os.close(self.stderr_write)
        except Exception as e:
            # TODO: custom exception
            raise Exception("Redirecting stdin, stdout, and stderr failed: %r" % e)

        try:
            if isinstance(argv, str):
                argv = [argv]

            if not enable_aslr:
                disable_self_aslr()
            
            if env:
                os.execve(argv[0], argv, env)
            else:
                os.execv(argv[0], argv)
        except OSError as e:
            liblog.debugger("Unable to execute %s: %s", argv, e)
            os._exit(1)

    
    def _setup_pipe(self):
        """
        Sets up the pipe manager for the child process.
        
        Close the read end for stdin and the write ends for stdout and stderr
        in the parent process since we are going to write to stdin and read from
        stdout and stderr
        """
        try:
            os.close(self.stdin_read)
            os.close(self.stdout_write)
            os.close(self.stderr_write)
        except Exception as e:
            # TODO: custom exception
            raise Exception("Closing fds failed: %r" % e)
        return PipeManager(self.stdin_write, self.stdout_read, self.stderr_read)

    def _setup_parent(self):
        """
        Sets up the parent process after the child process has been created or attached to.
        """
        liblog.debugger("Polling child process status")
        self.wait_for_child()
        liblog.debugger("Child process ready, setting options")
        self._set_options()
        liblog.debugger("Options set")
        invalidate_process_cache()
        self.hardware_bp_helper = ptrace_hardware_breakpoint_manager_provider(
            self._peek_user, self._poke_user, self._getregset, self._setregset
        )#TODO add here the methods for the add bphw for aaarch64 without pid

    def attach(self, process_id: int):
        """Attaches to the specified process.

        Args:
            process_id (int): The PID of the process to attach to.
        """
        # TODO: investigate errno handling
        result = self.lib_trace.ptrace_attach(process_id)
        if result == -1:
            errno_val = self.ffi.errno
            raise OSError(errno_val, errno.errorcode[errno_val])
        else:
            self.process_id = process_id
            liblog.debugger("Attached PtraceInterface to process %d", process_id)    
        self._setup_parent()


    def shutdown(self):
        """Shuts down the debugging backend."""
        if self.process_id is None:
            return

        try:
            os.kill(self.process_id, 9)
        except OSError:
            liblog.debugger("Process %d already dead", self.process_id)

        try:
            os.close(self.stdin_write)
            os.close(self.stdout_read)
            os.close(self.stderr_read)
        except Exception as e:
            liblog.debugger("Closing fds failed: %r", e)

        result = self.lib_trace.ptrace_detach(self.process_id)

        if result != -1:
            liblog.debugger("Detached PtraceInterface from process %d", self.process_id)
            os.wait()
        else:
            liblog.debugger("Unable to detach, process %d already dead", self.process_id)
        self.process_id = None

    def get_register_holder(self) -> RegisterHolder:
        """Returns the current value of all the available registers.
        Note: the register holder should then be used to automatically setup getters and setters for each register.
        """
        # TODO: this 512 is a magic number, it should be replaced with a constant
        register_file = self.ffi.new("char[512]")
        liblog.debugger("Getting registers from process %d", self.process_id)
        #TODO AARCH64   getsetregs
        architecure = platform.machine()
        if architecure == "x86_64":
            result = self.lib_trace.ptrace_getregs(self.process_id, register_file)
            if result == -1:
                errno_val = self.ffi.errno
                raise OSError(errno_val, errno.errorcode[errno_val])
            else:
                buffer = self.ffi.unpack(register_file, 512)
                return register_holder_provider(buffer, ptrace_setter=self._set_registers)
        elif architecure == "aarch64":
            SIZE = 0x110
            result = self.lib_trace.ptrace_getregset(self.process_id, NT_PRSTATUS, register_file, SIZE)
            if result == -1:
                errno_val = self.ffi.errno
                raise OSError(errno_val, errno.errorcode[errno_val])
            else:
                buffer = self.ffi.unpack(register_file, 512)
                return register_holder_provider(buffer, ptrace_setter=self._set_registers)
        else:
            raise NotImplementedError(f"Architecture {architecure} not supported")
        

    def _set_registers(self, buffer):
        """Sets the value of all the available registers."""
        # TODO: this 512 is a magic number, it should be replaced with a constant
        register_file = self.ffi.new("char[512]", buffer)
        architecure = platform.machine()
        if architecure == "x86_64":
            result = self.lib_trace.ptrace_setregs(self.process_id, register_file)
            if result == -1:
                errno_val = self.ffi.errno
                raise OSError(errno_val, errno.errorcode[errno_val])
        elif architecure == "aarch64":
            SIZE = 0x110
            result = self.lib_trace.ptrace_setregset(self.process_id, NT_PRSTATUS, register_file, SIZE)
            if result == -1:
                errno_val = self.ffi.errno
                raise OSError(errno_val, errno.errorcode[errno_val])
        else:
            raise NotImplementedError(f"Architecture {architecure} not supported")

    def wait_for_child(self):
        """Waits for the child process to be ready for commands.

        Returns:
            bool: Whether the child process is still alive.
        """
        assert self.process_id is not None
        # TODO: check what option this is, because I can't find it anywhere
        pid, status = os.waitpid(self.process_id, 1 << 30)
        liblog.debugger("Child process %d reported status %d", pid, status)

        if os.WIFEXITED(status):
            liblog.debugger("Child process %d exited with status %d", pid, status)

        if os.WIFSIGNALED(status):
            liblog.debugger("Child process %d exited with signal %d", pid, status)

        if os.WIFSTOPPED(status):
            liblog.debugger("Child process %d stopped with signal %d", pid, status)
            try:
                exitcode = os.waitstatus_to_exitcode(status)
                liblog.debugger("Child process %d exit code %d", pid, exitcode)
            except ValueError:
                pass

        return os.WIFSTOPPED(status)

    def provide_memory_view(self) -> MemoryView:
        """Returns a memory view of the process."""
        assert self.process_id is not None

        def getter(address) -> bytes:
            return self._peek_mem(address).to_bytes(8, "little", signed=False)

        def setter(address, value):
            self._poke_mem(address, int.from_bytes(value, "little", signed=False))

        return MemoryView(getter, setter, self.maps)

    def ensure_stopped(self):
        """Ensures that the process is stopped."""
        os.kill(self.process_id, signal.SIGSTOP)

    def continue_execution(self):
        """Continues the execution of the process."""
        assert self.process_id is not None
        result = self.lib_trace.ptrace_cont(self.process_id)

        # TODO: investigate errno handling
        if result == -1:
            errno_val = self.ffi.errno
            raise OSError(errno_val, errno.errorcode[errno_val])

        invalidate_process_cache()

    def continue_after_breakpoint(self, breakpoint: Breakpoint):
        """Continues the execution of the process after a breakpoint was hit."""
        if breakpoint.hardware:
            architecure = platform.machine()
            if architecure == "x86_64":
                self.continue_execution()
            elif architecure == "aarch64":
                assert self.process_id is not None
                result = self.lib_trace.ptrace_cont_after_hw_bp(
                    self.process_id,
                    breakpoint.address
                )
                if result == -1:
                    errno_val = self.ffi.errno
                    raise OSError(errno_val, errno.errorcode[errno_val])
            return

        assert self.process_id is not None
        assert breakpoint.address in self.software_breakpoints

        instruction = self.software_breakpoints[breakpoint.address]
        #TODO invalid code for aarch64 (CC is an x86 instruction)
        result = -1
        if architecure == "x86_64":
            result = self.lib_trace.cont_after_bp(
                self.process_id,
                breakpoint.address,
                instruction,
                (instruction & ((2**56 - 1) << 8)) | 0xCC,
            )

            if result == -1:
                errno_val = self.ffi.errno
                raise OSError(errno_val, errno.errorcode[errno_val])
        elif architecure == "aarch64":
            result = self.lib_trace.cont_after_bp(
                self.process_id,
                breakpoint.address,
                instruction,
                0xD4200000, # This is the 32-bit BRK instruction for AArch64
            )
        else:
            raise NotImplementedError(f"Architecture {architecure} not supported")

        if result == -1:
            errno_val = self.ffi.errno
            raise OSError(errno_val, errno.errorcode[errno_val])

        invalidate_process_cache()

    def _set_sw_breakpoint(self, address: int):
        """Sets a software breakpoint at the specified address.

        Args:
            address (int): The address where the breakpoint should be set.
        """
        assert self.process_id is not None
        instruction = self._peek_mem(address)
        self.software_breakpoints[address] = instruction

        architecure = platform.machine()
        if architecure == "x86_64":
            # TODO: this is not correct for all architectures
            self._poke_mem(address, (instruction & ((2**56 - 1) << 8)) | 0xCC)
        elif architecure == "aarch64":
            print("Setting software breakpoint at address 0x{:x}".format(address))
            # Replace the instruction with the AArch64 BRK #0xF000 (encoded as 0xD4200000)
            brk_instruction = 0xD4200000  # This is the 32-bit BRK instruction for AArch64
            
            # Write the BRK instruction to the memory at the given address
            self._poke_mem(address, brk_instruction)

        else:
            raise NotImplementedError(f"Architecture {architecure} not supported")

    def _unset_sw_breakpoint(self, address: int):
        """Unsets a software breakpoint at the specified address.

        Args:
            address (int): The address where the breakpoint should be unset.
        """
        assert self.process_id is not None
        self._poke_mem(address, self.software_breakpoints[address])

    def set_breakpoint(self, breakpoint: Breakpoint):
        """Sets a breakpoint at the specified address.

        Args:
            breakpoint (Breakpoint): The breakpoint to set.
        """
        if breakpoint.hardware:
            self.hardware_bp_helper.install_breakpoint(breakpoint)
        else:
            self._set_sw_breakpoint(breakpoint.address)

    def restore_breakpoint(self, breakpoint: Breakpoint):
        """Restores the breakpoint at the specified address.

        Args:
            address (int): The address where the breakpoint should be restored.
        """
        if breakpoint.hardware:
            self.hardware_bp_helper.remove_breakpoint(breakpoint)
        else:
            self._unset_sw_breakpoint(breakpoint.address)

    def step_execution(self):
        """Executes a single instruction before stopping again."""
        assert self.process_id is not None

        result = self.lib_trace.ptrace_singlestep(self.process_id)
        # TODO: investigate errno handling
        if result == -1:
            errno_val = self.ffi.errno
            raise OSError(errno_val, errno.errorcode[errno_val])

        invalidate_process_cache()

    def _peek_mem(self, address: int) -> int:
        """Reads the memory at the specified address."""
        assert self.process_id is not None

        result = self.lib_trace.ptrace_peekdata(self.process_id, address)
        liblog.debugger("PEEKDATA at address %d returned with result %x", address, result)

        error = self.ffi.errno
        if error == errno.EIO:
            raise OSError(error, errno.errorcode[error])

        return result

    def _poke_mem(self, address: int, value: int):
        """Writes the memory at the specified address."""
        assert self.process_id is not None

        result = self.lib_trace.ptrace_pokedata(self.process_id, address, value)
        liblog.debugger("POKEDATA at address %d returned with result %d", address, result)

        error = self.ffi.errno
        if error == errno.EIO:
            raise OSError(error, errno.errorcode[error])

    def _peek_user(self, address: int) -> int:
        """Reads the memory at the specified address."""
        assert self.process_id is not None

        result = self.lib_trace.ptrace_peekuser(self.process_id, address)
        liblog.debugger("PEEKUSER at address %d returned with result %x", address, result)

        error = self.ffi.errno
        if error == errno.EIO:
            raise OSError(error, errno.errorcode[error])

        return result

    def _poke_user(self, address: int, value: int):
        """Writes the memory at the specified address."""
        assert self.process_id is not None

        result = self.lib_trace.ptrace_pokeuser(self.process_id, address, value)
        liblog.debugger("POKEUSER at address %d returned with result %d", address, result)

        error = self.ffi.errno
        if error == errno.EIO:
            raise OSError(error, errno.errorcode[error])
#TODO add here the methods for the add bphw for aaarch64 that adds the pid and do the thing
# getregesetrs and setregset
    def _getregset(self, type: int, regset: "ctype", size: int):
        """Gets the registers from the process."""
        assert self.process_id is not None
        result = self.lib_trace.ptrace_getregset(self.process_id, type, regset, size)
        liblog.debugger("GETREGSET returned with result %d", result)
        error = self.ffi.errno
        if error == errno.EIO:
            raise OSError(error, errno.errorcode[error])
        return result
    
    def _setregset(self, type: int, regset: "ctype", size: int):
        """Sets the registers in the process."""
        assert self.process_id is not None

        result = self.lib_trace.ptrace_setregset(self.process_id, type, regset, size)
        liblog.debugger("SETREGSET returned with result %d", result)
        error = self.ffi.errno
        if error == errno.EIO:
            raise OSError(error, errno.errorcode[error])
        return result
        
    def fds(self):
        """Returns the file descriptors of the process."""
        assert self.process_id is not None
        return get_open_fds(self.process_id)

    def maps(self):
        """Returns the memory maps of the process."""
        assert self.process_id is not None
        return get_process_maps(self.process_id)

    def base_address(self):
        """Returns the base address of the process."""
        assert self.process_id is not None
        return guess_base_address(self.process_id)

    def is_pie(self):
        """Returns whether the executable is PIE or not."""
        assert self.process_id is not None
        return is_pie(self.argv[0])

    def resolve_address(self, address: int) -> int:
        """Normalizes and validates the specified address.

        Args:
            address (int): The address to normalize and validate.

        Returns:
            int: The normalized and validated address.

        Throws:
            ValueError: If the address is not valid.
        """
        maps = self.maps()
        return normalize_and_validate_address(address, maps)
