#include <bits/stdc++.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <sys/types.h>

#define CHECK(var, fn) do { if ((var) == -1) { perror(fn); exit(1); } } while (false)

using namespace std;

namespace {

int N, realStdout;
bool interact = false;

void writeToFd(int fd, const string& buf) {
	const char* ptr = buf.data();
	size_t len = buf.size();
	while (len > 0) {
		ssize_t w = write(fd, ptr, len);
		if (w == -1 && errno == EINTR) continue;
		if (w == -1 && errno == EPIPE) break;
		CHECK(w, "write");
		len -= w;
		ptr += w;
	}
}

string readFromFd(int fd) {
	char buf[1 << 20];
	string ret;
	for (;;) {
		ssize_t r = read(fd, buf, sizeof(buf));
		if (r == -1 && errno == EINTR) continue;
		if (r == 0) break;
		CHECK(r, "read");
		ret.insert(ret.end(), buf, buf + r);
	}
	return ret;
}

[[noreturn]]
void printAndExit(string msg) {
	msg += "\n";
	writeToFd(realStdout, msg);
	exit(0);
}

int parseInt(const string& s, const char* what, int lo, int hi) {
	// parse a base-10 number, ignoring leading/trailing spaces
	istringstream iss(s);
	int ret;
	string more;
	if (!(iss >> ret) || (iss >> more)) {
		printAndExit(string("failed to parse ") + what + " as integer: " + s);
	}
	if (!(lo <= ret && ret <= hi)) {
		printAndExit(string(what) + " out of bounds: " + to_string(ret) +
				" not in [" + to_string(lo) + ", " + to_string(hi) + "]");
	}
	return ret;
}

string waitForChild(int pid, int readFd, bool doneReading = false) {
	string buf;
	if (!doneReading)
		buf = readFromFd(readFd);

	int status;
	CHECK(waitpid(pid, &status, 0), "waitpid");
	if (WIFSIGNALED(status)) {
		// propagate the signal, or if not possible at least exit with an error
		CHECK(kill(getpid(), WTERMSIG(status)), "kill");
		exit(1);
	}
	int ex = WEXITSTATUS(status);
	if (ex != 0)
		exit(ex);

	CHECK(close(readFd), "close");
	return buf;
}

[[noreturn]]
void runSubmission(int in, int out) {
	CHECK(dup2(in, 0), "dup2");
	CHECK(dup2(out, 1), "dup2");
	// Throw an exception to resume execution at the end of real_main(),
	// after which main() will be called.
	throw true;
}

string runSubmissionStaticInput(const vector<string>& lines) {
	int pipefds[2];
	CHECK(pipe(pipefds), "pipe");
	int c2pRead = pipefds[0], c2pWrite = pipefds[1];
	CHECK(pipe(pipefds), "pipe");
	int p2cRead = pipefds[0], p2cWrite = pipefds[1];
	CHECK(fcntl(p2cRead, F_SETPIPE_SZ, 1024 * 1024), "fcntl");
	pid_t pid = fork();
	CHECK(pid, "fork");

	if (pid == 0) {
		CHECK(close(c2pRead), "close");
		CHECK(close(p2cWrite), "close");

		runSubmission(p2cRead, c2pWrite);
	} else {
		CHECK(close(p2cRead), "close");
		CHECK(close(c2pWrite), "close");

		string combined;
		for (const string& line : lines) {
			combined += line;
			combined += '\n';
		}

		writeToFd(p2cWrite, combined);
		CHECK(close(p2cWrite), "close");
		return waitForChild(pid, c2pRead);
	}
}

string runSubmissionInteractively(const vector<string>& lines) {
	int pipefds[2];
	CHECK(pipe(pipefds), "pipe");
	int c2pRead = pipefds[0], c2pWrite = pipefds[1];
	CHECK(pipe(pipefds), "pipe");
	int p2cRead = pipefds[0], p2cWrite = pipefds[1];
	CHECK(fcntl(p2cRead, F_SETPIPE_SZ, 1024 * 1024), "fcntl");
	pid_t pid = fork();
	CHECK(pid, "fork");

	if (pid == 0) {
		CHECK(close(c2pRead), "close");
		CHECK(close(p2cWrite), "close");

		runSubmission(p2cRead, c2pWrite);
	} else {
		CHECK(close(p2cRead), "close");
		CHECK(close(c2pWrite), "close");

		char buf[32];
		string output;
		bool doneReading = false;
		int pendingLines = 0;
		for (const string& line : lines) {
			writeToFd(p2cWrite, line + '\n');
			pendingLines++;

			while (!doneReading && pendingLines > 0) {
				ssize_t r = read(c2pRead, buf, sizeof(buf));
				if (r == -1 && errno == EINTR) continue;
				if (r == 0) {
					doneReading = true;
					break;
				}
				CHECK(r, "read");
				output.insert(output.end(), buf, buf + r);
				pendingLines -= (int)count(buf, buf + r, '\n');
			}
		}
		CHECK(close(p2cWrite), "close");
		auto more = waitForChild(pid, c2pRead, doneReading);
		output.insert(output.end(), more.begin(), more.end());
		return output;
	}
}

pair<int, vector<int>> runPhase1(const vector<int>& order) {
	assert((int)order.size() == N-1);
	vector<string> lines = {
		"1 " + to_string(N)
	};
	lines.reserve(N);
	for (int x : order) {
		lines.push_back(to_string(x));
	}

	string output;
	if (interact) {
		output = runSubmissionInteractively(lines);
	} else {
		// We pull a trick here (for a majority of test cases) and put the
		// entire data in the pipe at once. This sounds like it could aid
		// cheating, but:
		//
		// a) no contestant will think that this could happen,
		// b) we check that running phase 1 twice results in the same
		//    response up to the point where the input sequences differ, and
		// c) we also run the submission interactively for one test case.
		//
		// This greatly improves performance, often making submissions run
		// for 0.06s instead of (walltime) 0.6s.
		output = runSubmissionStaticInput(lines);
	}

	lines.clear();
	size_t i = 0;
	while (i < output.size()) {
		size_t j = output.find('\n', i);
		if (j == string::npos) {
			j = output.size();
		}
		lines.push_back(output.substr(i, j - i));
		i = j + 1;
	}

	if (lines.size() != order.size() + 1) {
		printAndExit("wrong number of lines of output");
	}

	int K = parseInt(lines[0], "K", 1, 1'000'000);

	vector<int> values(order.size());
	for (size_t i = 0; i < order.size(); i++) {
		values[i] = parseInt(lines[i+1], "value", 1, K);
	}

	return {K, values};
}

__attribute__((constructor))
void real_main() try {
	const string ACCEPTED_MSG = "OK:cc4ffbf1a0f67de5b288";

	signal(SIGPIPE, SIG_IGN);

	istringstream judgeIn(readFromFd(0));
	judgeIn >> N;
	string mode;
	judgeIn >> mode;
	vector<int> order(N), seen(N);
	for (int i = 0; i < N; i++) {
		judgeIn >> order[i];
		assert(0 <= order[i] && order[i] < N);
		assert(!seen[order[i]]++);
	}
	int targetIndex = order.back();
	order.pop_back();
	if (mode == "interact") {
		interact = true;
		mode = "random";
	}
	int lastval = -1, forkat = -1, copyat = -1;
	if (mode == "random")
		judgeIn >> lastval;
	else if (mode == "fork")
		judgeIn >> forkat;
	else if (mode == "copy")
		judgeIn >> copyat;
	else
		assert(0);

	// send stdout to stderr for the user program
	realStdout = dup(1);
	CHECK(realStdout, "dup");
	CHECK(dup2(2, 1), "dup2");

	// redirect the stdin fd to make it slightly harder to read stdin twice
	CHECK(close(0), "close");
	CHECK(open("/dev/null", O_RDONLY), "open");

	int K;
	vector<int> values;
	tie(K, values) = runPhase1(order);

	vector<int> out(N);
	for (int i = 0; i < N-1; i++) {
		out[order[i]] = values[i];
	}

	if (mode == "fork") {
		order[forkat] = targetIndex;
		int K2;
		vector<int> values2;
		tie(K2, values2) = runPhase1(order);
		if (K != K2 || !std::equal(values.begin(), values.begin() + forkat, values2.begin())) {
			printAndExit("non-deterministic solution");
		}
		out[targetIndex] = values2[forkat];
	}
	else if (mode == "random") {
		lastval %= K;
		if (lastval < 0) lastval += K;
		lastval += 1;
		out[targetIndex] = lastval;
	}
	else if (mode == "copy") {
		out[targetIndex] = out[copyat];
	}
	else {
		assert(0);
	}

	string outStr;
	for (int x : out) {
		assert(1 <= x && x <= K);
		if (!outStr.empty()) outStr += ' ';
		outStr += to_string(x);
	}

	string output = runSubmissionStaticInput({
		"2 " + to_string(N),
		outStr,
	});

	istringstream iss(output);
	string tok;
	vector<string> guess;
	while (iss >> tok) {
		guess.push_back(tok);
	}

	if (guess.size() != 2) {
		printAndExit("must guess exactly two integers, but found " + to_string(guess.size()));
	}

	int guess1 = parseInt(guess[0], "guess 1", 0, N-1);
	int guess2 = parseInt(guess[1], "guess 2", 0, N-1);

	if (targetIndex == guess1 || targetIndex == guess2) {
		printAndExit(ACCEPTED_MSG + "\n" + to_string(K));
	} else {
		printAndExit("wrong guess: " + to_string(guess1) + ", " + to_string(guess2) + ", but expected " + to_string(targetIndex));
	}

	assert(0);
} catch (bool) {}

}
