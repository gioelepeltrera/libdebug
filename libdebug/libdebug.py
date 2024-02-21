#
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2023 - 2024 Roberto Alessandro Bertolini, Gabriele Digregorio.
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

from __future__ import annotations
from libdebug.data.breakpoint import Breakpoint
from libdebug.data.memory_view import MemoryView
from libdebug.state.process_context import ProcessContext
from libdebug.state.process.process_context_provider import provide_process_context
from libdebug.state.thread_context import ThreadContext
from libdebug.state.debugging_context import debugging_context
from libdebug.interfaces.interface_helper import provide_debugging_interface
from libdebug.liblog import liblog
import os
from queue import Queue
from threading import Thread
from typing import Callable


class Debugger:
    """The Debugger class is the main class of `libdebug`. It contains all the methods needed to run and interact with the process."""

    memory: MemoryView = None
    """The memory view of the process."""

    process_context: ProcessContext
    """The process context object."""

    breakpoints: dict[int, Breakpoint]
    """A dictionary of all the breakpoints set on the process. The keys are the absolute addresses of the breakpoints."""

    threads: dict[int, ThreadContext]
    """A dictionary of all the threads in the process. The keys are the thread IDs."""

    def __init__(self):
        """Do not use this constructor directly.
        Use the `debugger` function instead.
        """
        # validate that the binary exists
        if not os.path.isfile(debugging_context.argv[0]):
            raise RuntimeError("The specified binary file does not exist.")

        # instanced is True if and only if the process has been started and has not been killed yet
        self.instanced = False

        self.interface = provide_debugging_interface()
        debugging_context.debugging_interface = self.interface

        self.process_context = provide_process_context()

        # threading utilities
        self._polling_thread: Thread | None = None
        self._polling_thread_command_queue: Queue = Queue()

        self.breakpoints = debugging_context.breakpoints
        self.threads = debugging_context.threads

        self._start_processing_thread()

    def run(self):
        """Starts the process and waits for it to stop."""
        if self.instanced:
            liblog.debugger("Process already running, stopping it before restarting.")
            self.kill()

        self.instanced = True

        if not self._polling_thread_command_queue.empty():
            raise RuntimeError("Polling thread command queue not empty.")

        self._polling_thread_command_queue.put((self.__threaded_run, ()))

        # Wait for the background thread to signal "task done" before returning
        # We don't want any asynchronous behaviour here
        self._polling_thread_command_queue.join()

        assert debugging_context.pipe_manager is not None

        return debugging_context.pipe_manager

    def _start_processing_thread(self):
        """Starts the thread that will poll the traced process for state change."""
        # Set as daemon so that the Python interpreter can exit even if the thread is still running
        self._polling_thread = Thread(
            target=self._polling_thread_function,
            name="libdebug_polling_thread",
            daemon=True,
        )
        self._polling_thread.start()

    def kill(self):
        """Kills the process."""
        if not self.instanced:
            raise RuntimeError("Process not running, cannot kill.")

        self._polling_thread_command_queue.put((self.__threaded_kill, ()))

        # If the process is running, interrupt it
        self.process_context.interrupt()

        self.memory = None
        self.instanced = None
        self.process_context = None

        if debugging_context.pipe_manager is not None:
            debugging_context.pipe_manager.close()
            debugging_context.pipe_manager = None

        # Wait for the background thread to signal "task done" before returning
        # We don't want any asynchronous behaviour here
        self._polling_thread_command_queue.join()

    def cont(self):
        """Continues the process."""
        if not self.instanced:
            raise RuntimeError("Process not running, cannot continue.")

        if debugging_context.dead or debugging_context.running:
            raise RuntimeError("Process is dead or already running.")

        self._polling_thread_command_queue.put((self.__threaded_cont, ()))

        # Wait for the background thread to signal "task done" before returning
        # We don't want any asynchronous behaviour here
        self._polling_thread_command_queue.join()

    def wait(self):
        """Waits for the process to stop."""
        if not self.instanced:
            raise RuntimeError("Process not running, cannot wait.")

        if debugging_context.dead or not debugging_context.running:
            raise RuntimeError("Process is dead or not running.")

        self._polling_thread_command_queue.put((self.__threaded_wait, ()))

        # Wait for the background thread to signal "task done" before returning
        # We don't want any asynchronous behaviour here
        self._polling_thread_command_queue.join()

    def step(self):
        """Executes a single instruction of the process."""
        if not self.instanced:
            raise RuntimeError("Process not running, cannot step.")

        self._polling_thread_command_queue.put((self.__threaded_step, ()))
        self._polling_thread_command_queue.put((self.__threaded_wait, ()))

        # Wait for the background thread to signal "task done" before returning
        # We don't want any asynchronous behaviour here
        self._polling_thread_command_queue.join()

    def breakpoint(
        self,
        position: int | str,
        hardware: bool = False,
        callback: None | Callable[[Debugger, Breakpoint], None] = None,
    ) -> Breakpoint:
        """Sets a breakpoint at the specified location.

        Args:
            position (int | bytes): The location of the breakpoint.
            hardware (bool, optional): Whether the breakpoint should be hardware-assisted or purely software. Defaults to False.
        """
        if debugging_context.running:
            raise RuntimeError("Cannot set a breakpoint while the process is running.")

        if isinstance(position, str):
            address = self.process_context.resolve_symbol(position)
        else:
            address = self.process_context.resolve_address(position)
            position = address

        bp = Breakpoint(address, position, 0, hardware, callback)

        self._polling_thread_command_queue.put((self.__threaded_breakpoint, (bp,)))

        # Wait for the background thread to signal "task done" before returning
        # We don't want any asynchronous behaviour here
        self._polling_thread_command_queue.join()

        # the breakpoint should have been set by interface
        assert address in self.breakpoints and self.breakpoints[address] is bp

        return bp

    def _polling_thread_function(self):
        """This function is run in a thread. It is used to poll the process for state change."""
        while True:
            # Wait for the main thread to signal a command to execute
            command, args = self._polling_thread_command_queue.get()

            # Execute the command
            command(*args)

            # Signal that the command has been executed
            self._polling_thread_command_queue.task_done()

    def __threaded_run(self):
        liblog.debugger("Starting process %s.", debugging_context.argv[0])
        self.interface.run()

        debugging_context.set_stopped()

        # create and update main thread context
        main_thread = ThreadContext.new()
        debugging_context.insert_new_thread(main_thread)

        main_thread._poll_registers()

        # create memory view
        self.memory = self.interface.provide_memory_view()

    def __threaded_kill(self):
        liblog.debugger("Killing process %s.", debugging_context.argv[0])
        self.interface.kill()

    def __threaded_cont(self):
        liblog.debugger("Continuing process %s.", debugging_context.argv[0])
        self.interface.cont()
        debugging_context.set_running()

    def __threaded_breakpoint(self, bp: Breakpoint):
        liblog.debugger("Setting breakpoint at 0x%x.", bp.address)
        self.interface.set_breakpoint(bp)

    def __threaded_wait(self):
        liblog.debugger("Waiting for process %s to stop.", debugging_context.argv[0])
        self.interface.wait()

        debugging_context.set_stopped()

        # Update the state of the process and its threads
        keys = list(self.threads.keys())
        for thread_id in keys:
            if thread_id in self.threads:
                self.threads[thread_id]._poll_registers()

    def __threaded_step(self):
        liblog.debugger("Stepping process %s.", self.argv[0])
        self.interface.step()
        debugging_context.set_running()


def debugger(
    argv: str | list[str] = None, enable_aslr: bool = False, env: dict[str, str] = None
) -> Debugger:
    """This function is used to create a new `Debugger` object. It takes as input the location of the binary to debug and returns a `Debugger` object.

    Args:
        argv (str | list[str]): The location of the binary to debug, and any additional arguments to pass to it.
        enable_aslr (bool, optional): Whether to enable ASLR. Defaults to False.
        env (dict[str, str], optional): The environment variables to use. Defaults to None.

    Returns:
        Debugger: The `Debugger` object.
    """
    if isinstance(argv, str):
        argv = [argv]

    debugging_context.argv = argv
    debugging_context.env = env
    debugging_context.aslr_enabled = enable_aslr

    return Debugger()
