#
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2023 Roberto Alessandro Bertolini.
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

from cffi import FFI
import platform
ffibuilder = FFI()
ffibuilder.cdef(
    """
    int ptrace_trace_me(void);
    int ptrace_attach(int pid);
    int ptrace_detach(int pid);
    void ptrace_set_options(int pid);


    int ptrace_getregs(int pid, void *regs);
    int ptrace_setregs(int pid, void *regs);
    
    int ptrace_getregset(int pid, int type, void *regs, int size);
    int ptrace_setregset(int pid, int type, void *regs, int size);

    int ptrace_cont(int pid);
    int ptrace_singlestep(int pid);

    uint64_t ptrace_peekdata(int pid, uint64_t addr);
    uint64_t ptrace_pokedata(int pid, uint64_t addr, uint64_t data);
    uint64_t ptrace_peekuser(int pid, uint64_t addr);
    uint64_t ptrace_pokeuser(int pid, uint64_t addr, uint64_t data);


    int ptrace_cont_after_hw_bp(int pid, uint64_t addr, uint32_t control);
    int cont_after_bp(int pid, uint64_t addr, uint64_t prev_data, uint64_t data);
"""
)

if platform.machine() == "aarch64":
    ffibuilder.cdef(
        """
        struct user_hwdebug_state {
            unsigned int dbg_info;
            unsigned int pad;
            struct {
                unsigned long addr;
                unsigned int ctrl;
                unsigned int pad;
            } dbg_regs[...];
        };
    """
    )

ffibuilder.set_source(
    "libdebug.cffi._ptrace_cffi",
    """
#ifdef __aarch64__
#include <sys/uio.h>
#include <asm/ptrace.h> // For the aarch64 register structure
#include <elf.h> // Include the ELF header
#endif

#ifdef __riscv
#include <sys/uio.h>
#include <riscv64-linux-gnu/asm/ptrace.h>  // For the RISC-V register structure
#include <riscv64-linux-gnu/sys/ptrace.h>  // For system calls with ptrace
#include <elf.h>     
#endif

#include <sys/ptrace.h>

#define ARM_DBREGS_COUNT 6          // Adjust according to the specific ARM implementation
#define ARM_WATCHDB_COUNT 4         // Adjust according to the specific ARM implementation
#define USER_HWDEBUG_STATE_LEN 0x68 // Adjust according to the specific ARM implementation
#define USER_WATCH_STATE_LEN 0x48   // Adjust according to the specific ARM implementation
#include <sys/types.h>
#include <sys/wait.h>
#include <stdint.h>


int ptrace_trace_me(void)
{
    return ptrace(PTRACE_TRACEME, 0, NULL, NULL);
}

int ptrace_attach(int pid)
{
    return ptrace(PTRACE_ATTACH, pid, NULL, NULL);
}

int ptrace_detach(int pid)
{
    return ptrace(PTRACE_DETACH, pid, NULL, NULL);
}

void ptrace_set_options(int pid)
{
    int options = PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC | PTRACE_O_TRACEEXIT;
    ptrace(PTRACE_SETOPTIONS, pid, NULL, options);
}

int ptrace_getregset(int pid, int type,  void *regs, int size)
{    
    struct iovec iov = { regs, size};
    return ptrace(PTRACE_GETREGSET, pid, type, &iov);
}

int ptrace_setregset(int pid, int type, void *regs, int size)
{
    struct iovec iov = { regs, size };
    return ptrace(PTRACE_SETREGSET, pid, type, &iov);
}
#ifdef __aarch64__

int ptrace_getregs(int pid, void *regs)
{    
    printf("GETREGS_CFFI____________");
    return -1;
}

int ptrace_setregs(int pid, void *regs)
{    
    printf("SETREGS_CFFI_________");
    return-1;
}

#else
int ptrace_getregs(int pid, void *regs)
{
    return ptrace(PTRACE_GETREGS, pid, NULL, regs);
}

int ptrace_setregs(int pid, void *regs)
{
    return ptrace(PTRACE_SETREGS, pid, NULL, regs);
}
#endif

int ptrace_cont(int pid)
{   
    return ptrace(PTRACE_CONT, pid, NULL, NULL);
}

int ptrace_cont_after_hw_bp(int pid, uint64_t addr, uint32_t control)
{
#ifdef __aarch64__
    int condition = (control >> 3) & 0x3;
    //getregset, check the register, remove bp, singlestep, reinstate bp, cont
    struct user_hwdebug_state hwdebug;
    struct iovec iov = {
        .iov_base = &hwdebug,
        .iov_len = USER_HWDEBUG_STATE_LEN
    };
    unsigned int table = NT_ARM_HW_BREAK;
    int count  = ARM_DBREGS_COUNT;
    if (condition != 0){
        iov.iov_len = USER_WATCH_STATE_LEN;
        table = NT_ARM_HW_WATCH;
        count = ARM_WATCHDB_COUNT;
    }
    if (ptrace(PTRACE_GETREGSET, pid, table, &iov) == -1) {
        perror("PTRACE_GETREGSET failed");
        return -1;
    }
    // Find the register that contains the breakpoint
    int i;
    for (i = 0; i < count; i++) {
        if (hwdebug.dbg_regs[i].addr == addr) {
            break;
        }
    }
    if (i == count) {
        perror("Breakpoint not found");
    }
    // Remove the breakpoint
    hwdebug.dbg_regs[i].addr = 0;
    hwdebug.dbg_regs[i].ctrl = 0;
    if (ptrace(PTRACE_SETREGSET, pid, table, &iov) == -1) {
        perror("PTRACE_SETREGSET failed");
        return -1;
    }
    // Single-step the child
    if (ptrace(PTRACE_SINGLESTEP, pid, NULL, NULL) == -1) {
        perror("PTRACE_SINGLESTEP failed");
        return -1;
    }

        // Wait for the process to stop after single stepping
    int status;
    if (waitpid(pid, &status, 0) == -1) {
        perror("waitpid failed");
        return -1;
    }

    // Ensure the process stopped due to the single-step and not something else
    if (!WIFSTOPPED(status) || WSTOPSIG(status) != SIGTRAP) {
        perror("_____-Unexpected signal received__");
        return -1;
    }

    // Reinstall the breakpoint
    if (ptrace(PTRACE_GETREGSET, pid, table, &iov) == -1) {
        perror("PTRACE_GETREGSET2 failed");
        return -1;
    }

    hwdebug.dbg_regs[i].addr = addr;
    hwdebug.dbg_regs[i].ctrl = control;
    if (ptrace(PTRACE_SETREGSET, pid, table, &iov) == -1) {
        perror("PTRACE_SETREGSET failed");
        return -1;
    }
    // Continue the child
    if (ptrace(PTRACE_CONT, pid, NULL, NULL) == -1) {
        perror("PTRACE_CONT failed");
        return -1;
    }
    return 0;
#else
    return -1;
#endif
}

int ptrace_singlestep(int pid)
{
    return ptrace(PTRACE_SINGLESTEP, pid, NULL, NULL);
}

uint64_t ptrace_peekdata(int pid, uint64_t addr)
{
    return ptrace(PTRACE_PEEKDATA, pid, (void*) addr, NULL);
}

uint64_t ptrace_pokedata(int pid, uint64_t addr, uint64_t data)
{
    return ptrace(PTRACE_POKEDATA, pid, (void*) addr, data);
}

uint64_t ptrace_peekuser(int pid, uint64_t addr)
{
    return ptrace(PTRACE_PEEKUSER, pid, addr, NULL);
}

uint64_t ptrace_pokeuser(int pid, uint64_t addr, uint64_t data)
{
    return ptrace(PTRACE_POKEUSER, pid, addr, data);
}


//TODO CONTINUE AFTER SOFTWARE BREAKPOINT
int cont_after_bp(int pid, uint64_t addr, uint64_t prev_data, uint64_t data)
{
    int status;
    // restore the previous instruction
    status = ptrace(PTRACE_POKEDATA, pid, (void*) addr, prev_data);

    if (status == -1) {
        return status;
    }

    // step over the breakpoint
    status = ptrace(PTRACE_SINGLESTEP, pid, NULL, NULL);

    if (status == -1) {
        return status;
    }
    // wait for the child
    waitpid(pid, &status, 1 << 30);

    status = ptrace(PTRACE_POKEDATA, pid, (void*) addr, data);

    if (status == -1) {
        return status;
    }
    // continue the execution
    status = ptrace(PTRACE_CONT, pid, NULL, NULL);
    return status;
}
""",
    libraries=[],
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
