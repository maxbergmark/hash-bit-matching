#pragma once
#include "hash_types.cl"

void print_hash_input(inbuf inbuffer) {
	printf("%08x%08x%08x%08x%08x%08x%08x%08x (%d)\n", 
		SWAP(inbuffer.buffer[0]), 
		SWAP(inbuffer.buffer[1]), 
		SWAP(inbuffer.buffer[2]), 
		SWAP(inbuffer.buffer[3]),
		SWAP(inbuffer.buffer[4]),
		SWAP(inbuffer.buffer[5]),
		SWAP(inbuffer.buffer[6]),
		SWAP(inbuffer.buffer[7]),
		inbuffer.length
	);
}

void print_hash(outbuf outbuffer) {
	printf("%08x%08x%08x%08x%08x%08x%08x%08x\n", 
		SWAP(outbuffer.buffer[0]), 
		SWAP(outbuffer.buffer[1]), 
		SWAP(outbuffer.buffer[2]), 
		SWAP(outbuffer.buffer[3]),
		SWAP(outbuffer.buffer[4]),
		SWAP(outbuffer.buffer[5]),
		SWAP(outbuffer.buffer[6]),
		SWAP(outbuffer.buffer[7])
	);
}

void print_hash_match(outbuf outbuffer, int matching_bits) {
	const char OKGREEN[] = "\033[92m";
	const char YELLOW[] = "\033[93m";
	const char ENDC[] = "\033[0m";
	// printf("test\n");
	printf("%s", OKGREEN);
	for (int i = 0; i < 8; i++) {
		int n = outbuffer.buffer[i];
		for (int j = 0; j < 4; j++) {
			if (matching_bits < 8) {
				// printf("%s", ENDC);
				printf("%s", YELLOW);
			}
			if (matching_bits <= 0) {
				printf("%s", ENDC);
			}
			printf("%02x", n & 0xff);
			n >>= 8;
			matching_bits -= 8;
		}
	}
	printf("\n");
}

void print_hash_input_word(inbuf inbuffer) {
	char* c0 = (char*) &inbuffer.buffer[0];
	printf("%.12s\n", 
		c0
	);
}

void print_collision(inbuf original_input, outbuf outbuffer, 
	distinguished_point private_point, int j, int search_bits) {
	
	// printf("\nfound collision\n");
	char* orig_str = (char*) original_input.buffer;
	printf("\nself.verify(\"%.12s\", %d, \"%.12s\", %d, %d)\n\n", 
		orig_str, j, 
		private_point.hash_input, private_point.offset, search_bits);

}