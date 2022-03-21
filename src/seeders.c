#include <stdio.h>

const char* seeders[] = {
	// Testing unit
	// If more than 1, add newline
	// e.g
	// "+237672451860\n"};
	"+237672451860"};

const unsigned int num_seeders = sizeof(seeders)/sizeof(seeders[0]);


int main() {
	for(unsigned i=0;i<num_seeders;++i)
		printf("%s", seeders[i]);
	return 0;
}
