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

from libdebug.architectures.register_holder import RegisterHolder
from libdebug.data.breakpoint import Breakpoint
from libdebug.data.memory_view import MemoryView
from libdebug.interfaces.interface_helper import debugging_interface_provider
from libdebug.architectures.stack_unwinding_provider import stack_unwinding_provider
from libdebug.utils.debugging_utils import resolve_symbol_in_maps, resolve_address_in_maps
from libdebug.liblog import liblog
from queue import Queue
from typing import Callable
from threading import Thread, Event
import platform

class Debugger:
    """The Debugger class is the main class of `libdebug`. It contains all the methods needed to run and interact with the process."""

    registers: RegisterHolder | None = None
    """The register holder object. It provides access to all the registers of the stopped process."""

    breakpoints: dict[int, Breakpoint] = None
    """A dictionary of all the breakpoints set on the process. The keys are the absolute addresses of the breakpoints."""

    running: bool = False
    """True if and only if the process is currently running."""

    memory: MemoryView = None

    def __init__(self, argv, enable_aslr, env):
        """Do not use this constructor directly.
        Use the `debugger` function instead.
        """
        if isinstance(argv, str):
            self.argv = [argv]
        else:
            self.argv = argv

        self.enable_aslr = enable_aslr
        self.env = env

        # instanced is True if and only if the process has been started and has not been killed yet
        self.instanced = False

        # threading utilities
        self.polling_thread: Thread | None = None
        self.polling_thread_command_queue: Queue = Queue()
        self.polling_thread_start_event: Event = Event()

        # instance breakpoints dict
        self.breakpoints = {}

    def __del__(self):
        self.kill()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()
        return False

    def _poll_registers(self):
        """Updates the register values."""
        self.registers = self.interface.get_register_holder()
        self.registers.apply_on(self, Debugger)

    def _flush_registers(self):
        self.registers.flush(self)

    def _start_process(self):
        """
        Starts a new process.
        """
        assert self.argv is not None, "Process argv is empty"
        liblog.debugger("Starting process %s", self.argv[0])
        self.pipe_manager = self.interface.run(self.argv, self.enable_aslr, self.env)
        self._poll_registers()
        self.memory = self.interface.provide_memory_view()
        self.instanced = True
        self.polling_thread_start_event.set()


    def start(self):
        """Starts the process. This method must be called before any other method, and any time the 
        process needs to be restarted."""
        if self.instanced:
            self.kill()
            self.instanced = False
        
        self.running = False
        self.interface = debugging_interface_provider()
        self.stack_unwinding = stack_unwinding_provider()
        self._setup_polling_thread()

        self.polling_thread_start_event.clear()
        self.polling_thread_command_queue.put((self._start_process, ()))
        self.polling_thread_start_event.wait()

        return self.pipe_manager
    
    
    def _attach_process(self, process_id: int):
        """
        Attaches to an already running process.
        """
        liblog.debugger("Attaching process %s", process_id)
        self.interface.attach(process_id)
        self._poll_registers()
        self.memory = self.interface.provide_memory_view()
        self.instanced = True
        self.polling_thread_start_event.set()
    
    
    def attach(self, process_id: int):
        """Attaches to an already running process. This method or start must be called before any other 
        method, and any time the process needs to be restarted."""
        if self.instanced:
            self.kill()
        
        self.interface = debugging_interface_provider()
        self.stack_unwinding = stack_unwinding_provider()
        self._setup_polling_thread()

        self.polling_thread_start_event.clear()
        self.polling_thread_command_queue.put((self._attach_process, (process_id,)))
        self.polling_thread_start_event.wait()


    def kill(self):
        """Kills the process."""
        if self.polling_thread:
            self.polling_thread.join()
        self.interface.shutdown()
        self.polling_thread.join()
        self.instanced = False
        self.memory = None

    def _flush_and_cont_after_bp(self, breakpoint: Breakpoint):
        """Flushes the registers, resumes the execution of the process, and re-sets the breakpoint at the specified address."""
        self.registers.flush(self)
        self.interface.continue_after_breakpoint(breakpoint)
        self.running = True

    def _flush_and_cont(self):
        """Flushes the registers and continues the execution of the process."""
        self.registers.flush(self)
        self.interface.continue_execution()
        self.running = True

    def _flush_and_step(self):
        """Flushes the registers and executes a single instruction before stopping again."""
        self.registers.flush(self)
        self.interface.step_execution()
        self.running = True

    def cont(self):
        """Continues the execution of the process."""
        if self.running:
            raise RuntimeError("Cannot continue while the process is running.")

        self.polling_thread_command_queue.put((self._flush_and_cont, ()))

    def block(self):
        """Stops the execution of the process."""
        pass

    def step(self):
        """Executes a single instruction before stopping again."""
        if self.running:
            raise RuntimeError("Cannot step while the process is running.")

        self.polling_thread_command_queue.put((self._flush_and_step, ()))

    def b(
        self,
        position: int | str,
        callback: None | Callable[["Debugger", Breakpoint], None] = None,
        hardware_assisted: bool = False,
        condition: str = "X",
        length: int = 1,
    ):
        """Sets a breakpoint at the specified location. The callback will be executed when the breakpoint is hit.

        Args:
            location (int | bytes): The location of the breakpoint.
            callback (None | callable, optional): The callback to call when the breakpoint is hit. Defaults to None.
            hardware_assisted (bool, optional): Whether the breakpoint should be hardware-assisted or purely software. Defaults to False.
            length (int, optional): The length of the breakpoint. Defaults to 0 in x86, to 1 (halfword in aarch64). Options 
        """
        if self.running:
            raise RuntimeError("Cannot set a breakpoint while the process is running.")

        if isinstance(position, str):
            address = resolve_symbol_in_maps(position, self.maps())
        else:
            address = position
            position = None
        
        address = self.interface.resolve_address(address)

        breakpoint = Breakpoint(address, position, 0, hardware_assisted, callback, condition, length)

        self.breakpoints[address] = breakpoint

        self.polling_thread_command_queue.put(
            (self.interface.set_breakpoint, [breakpoint])
        )
        #TODO REMOVE
        #insert in print whether hw or sw
        print("LIBDEBUG: Breakpoint set at", hex(address))

    def jump(self, location: int | bytes):
        """Jumps to the specified location.

        Args:
            location (int | bytes): The location to jump to.
        """
        pass

    def maps(self):
        """Returns the memory maps of the process."""
        return self.interface.maps()
    
    def backtrace(self):
        """Returns the current backtrace of the process."""
        backtrace = self.stack_unwinding.unwind(self)
        return list(map(lambda x: resolve_address_in_maps(x, self.maps()), backtrace))

    def fds(self):
        """Returns the file descriptors of the process."""
        return self.interface.fds()

    def base_address(self):
        """Returns the base address of the process."""
        return self.interface.base_address()

    def _poll_and_run_on_process(self) -> bool:
        """Polls the process for changes and runs the callbacks on the process.

        Returns:
            bool: True if the process is still running, False otherwise.
        """
        liblog.debugger("Polling process for state change")

        if not self.interface.wait_for_child():
            # The process has exited
            return False

        self.running = False
        self._poll_registers()
        print("In _poll_and_run_on_process")
        print("RIP:", hex(self.rip))


        # TODO: this -1 is dependent on the architecture's instruction size and investigate this behavior
        # Sometimes the process stops at the instruction after the breakpoint
        if self.rip not in self.breakpoints and (self.rip - 1) in self.breakpoints:
            address = self.rip - 1
        else:
            address = self.rip

        if address in self.breakpoints:
            breakpoint = self.breakpoints[address]
            breakpoint.hit_count += 1

            # Restore RIP
            self.rip = address

            if breakpoint._callback:
                breakpoint._callback(self, breakpoint)
                self._empty_queue()

            self._flush_and_cont_after_bp(breakpoint)
        else:
            liblog.debugger("Stopped at %x but no breakpoint set, continuing", self.rip)
            print("Stopped at %x but no breakpoint set, continuing", self.rip)
            print("Value in registers:")
            regs = [self.x0, self.x1, self.x2, self.x3, self.x4, self.x5, self.x6, self.x7, self.x8]
            for reg in regs:
                print(hex(reg))
                if reg in self.breakpoints:
                    print("HEYYYYY Breakpoint set at", hex(reg))
                    breakpoint = self.breakpoints[reg]
                    breakpoint.hit_count += 1
                    if breakpoint._callback:
                        breakpoint._callback(self, breakpoint)
                        self._empty_queue()
                    self._flush_and_cont_after_bp(breakpoint)
                    return True
            self._flush_and_cont()
        print("End of _poll_and_run_on_process____")
        return True
    
    def _empty_queue(self):
        """
        Empties the command queue.
        """
        while not self.polling_thread_command_queue.empty():
            command, args = self.polling_thread_command_queue.get()
            command(*args)

    def _polling_thread_function(self):
        """The function executed by the polling thread."""
        while True:
            if not self.polling_thread_command_queue.empty():
                command, args = self.polling_thread_command_queue.get()
                command(*args)
            elif self.running:
                if not self._poll_and_run_on_process():
                    break

    def _setup_polling_thread(self):
        """Sets up the thread that polls the process for changes."""
        self.polling_thread = Thread(target=self._polling_thread_function)
        self.polling_thread.start()


def debugger(argv: str | list[str] = None, enable_aslr: bool = False, env: dict[str, str] = None) -> Debugger:
    """This function is used to create a new `Debugger` object. It takes as input the location of the binary to debug and returns a `Debugger` object.

    Args:
        argv (str | list[str]): The location of the binary to debug, and any additional arguments to pass to it.
        enable_aslr (bool, optional): Whether to enable ASLR. Defaults to False.
        env (dict[str, str], optional): The environment variables to use. Defaults to None.

    Returns:
        Debugger: The `Debugger` object.
    """

    return Debugger(argv, enable_aslr, env)
