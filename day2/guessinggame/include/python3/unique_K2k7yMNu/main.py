#!/usr/bin/env python3
from fcntl import fcntl
from io import StringIO
import os
import runpy
import sys
import struct
from typing import List, Tuple


def judge_main() -> None:
    ACCEPTED_MSG = "OK:cc4ffbf1a0f67de5b288"
    F_SETPIPE_SZ = 1031

    # Identify the submission file
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    relevant_files = []
    for dname, dirs, files in os.walk(parent_dir):
        if "unique_K2k7yMNu" in dname:
            continue
        for fname in files:
            if fname.endswith(".py"):
                relevant_files.append(os.path.join(dname, fname))
    assert len(relevant_files) == 1, "must be exactly one Python file in submission"
    sub_file = relevant_files[0]

    N = int(input())
    mode = input()
    order = list(map(int, input().split()))
    assert sorted(order) == list(range(N))
    target_index = order[-1]
    order.pop();
    interact = False
    if mode == "interact":
        interact = True
        mode = "random"
    if mode == "random":
        lastval = int(input())
    elif mode == "fork":
        forkat = int(input())
    elif mode == "copy":
        copyat = int(input())
    else:
        assert False, mode

    # send stdout to stderr for the user program
    real_stdout = os.fdopen(os.dup(1), "w", closefd=False)
    os.dup2(2, 1)

    # redirect the stdin fd to make it slightly harder to read stdin twice
    os.close(0)
    os.open("/dev/null", os.O_RDONLY)

    def print_and_exit(msg: str):
        real_stdout.write(msg + "\n")
        sys.exit(0)

    def parse_int(s: str, what: str, lo: int, hi: int) -> int:
        # parse a base-10 number, ignoring leading/trailing spaces
        try:
            ret = int(s)
        except Exception:
            print_and_exit(f"failed to parse {what} as integer: {s}")
        if not (lo <= ret <= hi):
            print_and_exit(f"{what} out of bounds: {ret} not in [{lo}, {hi}]")
        return ret


    def wait_for_child(pid: int, read_fd: int, done_reading: bool = False) -> bytes:
        # Read everything the other process writes, until it terminates (or at
        # least closes the pipe write end).
        buf = b""
        if not done_reading:
            with os.fdopen(read_fd, "rb", closefd=False) as f:
                buf = f.read()

        pid, status = os.waitpid(pid, 0)
        if os.WIFSIGNALED(status):
            # propagate the signal, or if not possible at least exit with an error
            os.kill(os.getpid(), os.WTERMSIG(status))
            sys.exit(1)
        ex = os.WEXITSTATUS(status)
        if ex != 0:
            sys.exit(ex)

        os.close(read_fd)
        return buf

    def run_submission_static_input(lines: List[str]) -> bytes:
        """Run the submission with a given input string, returning the output."""
        # CPython and Pypy don't currently use threads, so using fork without exec
        # here is safe.
        c2p_read, p2c_write = os.pipe()
        pid = os.fork()

        if pid == 0:
            os.close(c2p_read)

            # Use string IO objects to redirect stdio, for improved performance
            # compared to pipes.
            out = StringIO()
            sys.stdin = StringIO("\n".join(lines) + "\n")
            sys.stdout = out

            try:
                runpy.run_path(sub_file, {}, "__main__")
                sys.exit(0)
            finally:
                data = out.getvalue().encode("utf-8")
                with os.fdopen(p2c_write, "wb") as f:
                    f.write(data)
        else:
            os.close(p2c_write)
            return wait_for_child(pid, c2p_read)

    def run_submission_interactively(lines: List[str]) -> bytes:
        """Run the submission and alternatingly write and read lines, returning the output."""
        # CPython and Pypy don't currently use threads, so using fork without exec
        # here is safe.
        c2p_read, c2p_write = os.pipe()
        p2c_read, p2c_write = os.pipe()
        fcntl(p2c_read, F_SETPIPE_SZ, 1024 * 1024)
        pid = os.fork()

        if pid == 0:
            os.close(p2c_write)
            os.close(c2p_read)

            os.dup2(p2c_read, 0)
            os.dup2(c2p_write, 1)

            runpy.run_path(sub_file, {}, "__main__")
            sys.exit(0)
        else:
            os.close(c2p_write)
            os.close(p2c_read)

            output = []
            done_reading = False
            with os.fdopen(p2c_write, "wb", buffering=0) as fout:
                pending_lines = 0
                for line in lines:
                    try:
                        fout.write(line.encode("ascii") + b"\n")
                    except BrokenPipeError:
                        pass
                    pending_lines += 1
                    while not done_reading and pending_lines > 0:
                        data = os.read(c2p_read, 32)
                        if not data:
                            done_reading = True
                            break
                        output.append(data)
                        pending_lines -= data.count(b"\n")

            output.append(wait_for_child(pid, c2p_read, done_reading))
            return b"".join(output)

    def run_phase1(order: List[int]) -> Tuple[int, List[int]]:
        assert len(order) == N-1
        lines = [f"1 {N}", *map(str, order)]

        if interact:
            enc_output = run_submission_interactively(lines)
        else:
            # We pull a trick here (for a majority of test cases) and put the
            # entire data in the pipe at once. This sounds like it could aid
            # cheating, but:
            #
            # a) no contestant will think that this could happen,
            # b) we check that running phase 1 twice results in the same
            #    response up to the point where the input sequences differ, and
            # c) we also run the submission interactively for one test case.
            #
            # This greatly improves performance, often making submissions run
            # for 0.1s instead of (walltime) 0.7s.
            enc_output = run_submission_static_input(lines)

        output = enc_output.decode("latin1")
        lines = output.splitlines()
        if len(lines) != len(order) + 1:
            print_and_exit(f"wrong number of lines of output")

        K = parse_int(lines[0], "K", 1, 10**6)

        values = []
        for i in range(len(order)):
            values.append(parse_int(lines[i+1], "value", 1, K))

        return K, values

    K, values = run_phase1(order)

    out = [0] * N
    for i in range(N-1):
        out[order[i]] = values[i]

    if mode == "fork":
        order[forkat] = target_index
        K2, values2 = run_phase1(order)
        if K2 != K or values[:forkat] != values2[:forkat]:
            print_and_exit("non-deterministic submission")
        out[target_index] = values2[forkat]

    elif mode == "random":
        lastval %= K
        lastval += 1
        out[target_index] = lastval

    elif mode == "copy":
        out[target_index] = out[copyat]

    else:
        assert False, mode

    for x in out:
        assert 1 <= x <= K

    output = run_submission_static_input([
        f"2 {N}",
        " ".join(map(str, out)),
    ])

    guess = output.decode("latin1").split()
    if len(guess) != 2:
        print_and_exit(f"must guess exactly two integers, but found {len(guess)}")
    guess1 = parse_int(guess[0], "guess 1", 0, N-1)
    guess2 = parse_int(guess[1], "guess 2", 0, N-1)

    if target_index == guess1 or target_index == guess2:
        print_and_exit(f"{ACCEPTED_MSG}\n{K}")
    else:
        print_and_exit(f"wrong guess: {guess1}, {guess2}, but expected {target_index}")

if __name__ == "__main__":
    judge_main()
