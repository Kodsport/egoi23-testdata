#include "validate.h"

#include <string>
#include <cmath>
using namespace std;

// All the real validation is done by the code in include/ that gets compiled
// together with the submission. All we do here is scoring.

int main(int argc, char **argv) {
	init_io(argc, argv);

	int N;
	judge_in >> N;
	assert(judge_in);

	string line;
	getline(author_out, line);

	if (!author_out || line != "OK:cc4ffbf1a0f67de5b288") {
		wrong_answer("%s\n", line.c_str());
	}

	int k;
	author_out >> k;
	if (!author_out) judge_error("eof?");

	int score;
	if (N == 4) {
		// sample
		score = 0;
	} else {
		assert(N == 100'000);
		if (k <= 30) score = min(77 + (30 - k), 100);
		else if (k <= 10000) score = (int)(46 + 31 * (4 - log10(k)) / (4 - log10(30)));
		else if (k < N-1) score = 10 + (int)(40 * (1 - (double)k / N));
		else score = 10;
	}

	accept_with_score(score);
}
