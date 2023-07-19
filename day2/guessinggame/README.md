The grader for guessinggame is a bit complex. The way it works is that the
order of houses is fixed per testcase, but the value Emma writes on her own
house is chosen adaptively. The second line of each .in file explains how
the value gets chosen for that test case:

- `random`: the last line of the input file contains a number X. The value is
  chosen as X % K + 1.
- `interact`: same as random, except that the judging is performed
  interactively, instead of non-interactively for performance. This is an
  implementation detail which should not matter. See includes/ for more details
  if curious.
- `copy`: the last line of the input file contains a number X. The value is
  copied from house with index X.
- `fork`: the last line of the input file contains a number X. Phase 1 of the
  submission is run as a trial run with Emma's house placed at (0-based) position
  X of the house visit order, and the house that was originally at position X
  removed. Let the number that Anna writes on that house be Y. Then in the real
  run of phase 1, Emma writes the number Y on her house.

  That is Emma, essentially asks Anna "if we had visited my house at time X,
  what number would you have written on it?".

The grading is performed by adding a file that gets compiled/run together with
the submission and uses the fork() function to make it run multiple times.
