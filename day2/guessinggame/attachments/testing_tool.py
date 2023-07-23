#!/usr/bin/env python3

"""
Example usage (with N=4, s=2, random order, where s is the number written on the last house):

For python programs, say "solution.py" (normally run as "pypy3 solution.py"):

    python3 testing_tool.py pypy3 solution.py <<<"4 2"

For C++ programs, first compile it
(e.g. with "g++ -std=gnu++17 solution.cpp -o solution.out")
and then run

    python3 testing_tool.py ./solution.out <<<"4 2"

"""

from fcntl import fcntl
import random
import sys
import os
import signal
from collections import Counter
from typing import List, Tuple

F_SETPIPE_SZ = 1031


def error(msg: str) -> None:
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)

def parse_int(s: str, what: str, lo: int, hi: int) -> int:
    try:
        ret = int(s)
    except Exception:
        error(f"Failed to parse {what} as integer: {s}")
    if not (lo <= ret <= hi):
        error(f"{what} out of bounds: {ret} not in [{lo}, {hi}]")
    return ret

def wait_for_child(pid: int) -> None:
    pid, status = os.waitpid(pid, 0)
    if os.WIFSIGNALED(status):
        sig = os.WTERMSIG(status)
        error(f"Program terminated with signal {sig} ({signal.Signals(sig).name})")
    ex = os.WEXITSTATUS(status)
    if ex != 0:
        error(f"Program terminated with exit code {ex}")

def read_line(pid: int, file, what: str) -> str:
    line = file.readline()
    if not line:
        wait_for_child(pid)
        error(f"Failed to read {what}: no more output")
    return line.rstrip("\r\n")

def write_line(file, line: str) -> None:
    try:
        file.write(line + "\n")
        file.flush()
    except BrokenPipeError:
        pass

def run_phase1(submission: List[str], indices: List[int], last_value: int, silent: bool) -> List[int]:
    n = len(indices)

    c2p_read, c2p_write = os.pipe()
    p2c_read, p2c_write = os.pipe()
    try:
        fcntl(p2c_read, F_SETPIPE_SZ, 1024 * 1024)
    except Exception:
        print("Warning: failed to increase pipe capacity. This may lead to hangs.")
    pid = os.fork()

    if pid == 0:
        os.close(p2c_write)
        os.close(c2p_read)

        os.dup2(p2c_read, 0)
        os.dup2(c2p_write, 1)

        try:
            os.execvp(submission[0], submission)
        except Exception as e:
            error(f"Failed to execute program: {e}")
        assert False, "unreachable"
    else:
        os.close(c2p_write)
        os.close(p2c_read)

        vals = [-1] * n
        with os.fdopen(p2c_write, "w") as fout:
            with os.fdopen(c2p_read, "r") as fin:
                write_line(fout, f"1 {n}")
                kline = read_line(pid, fin, "K")
                k = parse_int(kline, "K", 1, 10**6)
                if not silent:
                    print(f"[*] Got K = {k}")
                if last_value < 1 or last_value > k:
                    error(f"The value provided for the last value was {last_value}, which is not between 1 and K (K = {k})")
                for index in indices[:-1]:
                    write_line(fout, str(index))
                    line2 = read_line(pid, fin, "value")
                    vals[index] = parse_int(line2, "Value", 1, k)
                    if not silent:
                        print(f"[*] {index} => {vals[index]}")

                # Wait for program to terminate, and read all its output
                remainder = fin.read()
                if remainder.strip():
                    error(f"Unexpected trailing output: {remainder}")
                try:
                    fin.close()
                except BrokenPipeError:
                    pass
                try:
                    fout.close()
                except BrokenPipeError:
                    pass

        wait_for_child(pid)
        vals[indices[-1]] = last_value
        if not silent:
            print(f"[*] {indices[-1]} => {last_value} (secret)")
        return vals

def run_phase2(submission: List[str], values: List[int], silent: bool) -> Tuple[int, int]:
    n = len(values)

    c2p_read, c2p_write = os.pipe()
    p2c_read, p2c_write = os.pipe()
    try:
        fcntl(p2c_read, F_SETPIPE_SZ, 1024 * 1024)
    except Exception:
        print("Warning: failed to increase pipe capacity. This may lead to hangs.")
    pid = os.fork()

    if pid == 0:
        os.close(p2c_write)
        os.close(c2p_read)

        os.dup2(p2c_read, 0)
        os.dup2(c2p_write, 1)

        try:
            os.execvp(submission[0], submission)
        except Exception as e:
            error(f"Failed to execute program: {e}")
        assert False, "unreachable"
    else:
        os.close(c2p_write)
        os.close(p2c_read)

        with os.fdopen(p2c_write, "w") as fout:
            with os.fdopen(c2p_read, "r") as fin:
                write_line(fout, f"2 {n}")
                write_line(fout, " ".join(map(str, values)))
                guess_line = read_line(pid, fin, "guess")
                guess = guess_line.split()
                if len(guess) != 2:
                    error(f"Output must be exactly two integers, but found: {guess_line}")
                guess1 = parse_int(guess[0], "Guess 1", 0, n-1)
                guess2 = parse_int(guess[1], "Guess 2", 0, n-1)

                # Wait for program to terminate, and read all its output
                remainder = fin.read()
                if remainder.strip():
                    error(f"Unexpected trailing output: {remainder}")
                try:
                    fin.close()
                except BrokenPipeError:
                    pass
                try:
                    fout.close()
                except BrokenPipeError:
                    pass

        wait_for_child(pid)
        return guess1, guess2

def main() -> None:
    silent = False
    args = sys.argv[1:]
    if args and args[0] == "--silent":
        args = args[1:]
        silent = True
    if not args:
        print("Usage:", sys.argv[0], "[--silent] program... <input.txt")
        sys.exit(0)

    toks = []
    for line in sys.stdin:
        for tok in line.split():
            toks.append(int(tok))
        if toks and len(toks) >= 2:
            break

    if len(toks) != 2:
        error("Need exactly 2 input parameters: N s")
    n, last_value = toks[0], toks[1]

    if n < 1:
        error("N must be at least one")

    indices = []
    for i in range(n):
        indices.append(i)
    random.shuffle(indices)

    # MODIFY HERE to use a hard-coded house order:
    # indices = [3, 2, 1, 0]

    if len(indices) != n:
        error(f"Indices has wrong length: got {len(indices)} but expected {n}")

    extra = sorted(set(indices) - set(range(n)))
    if extra:
        error(f"Indices mentions house number outside of 0, ..., n-1: {extra[0]}")

    which, count = Counter(indices).most_common(1)[0]
    if count > 1:
        error(f"Not a permutation: index {which} is mentioned twice")

    if not silent:
        if len(indices) <= 10:
            perm_str = ", ".join(map(str, indices))
        else:
            perm_str = ", ".join(map(str, indices[:4])) + ", ..., " + ", ".join(map(str, indices[-4:]))
        print(f"[*] Running phase 1 (N = {n}, last value = {last_value}, house order = {perm_str})")


    vals = run_phase1(args, indices, last_value, silent)

    if not silent:
        print(f"[*] Running phase 2")

    guess1, guess2 = run_phase2(args, vals, silent)

    if indices[-1] in (guess1, guess2):
        print(f"[*] OK: guessed {guess1}, {guess2}, answer was {indices[-1]}")
    else:
        print(f"[*] Wrong Answer: guessed {guess1}, {guess2}, but answer was {indices[-1]}")

if __name__ == "__main__":
    main()
