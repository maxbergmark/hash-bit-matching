

ulong get_long_from_hash(outbuf outbuffer, int bits) {
	ulong res = 0;
	res |= SWAP(outbuffer.buffer[0]);
	res <<= 32;
	res |= SWAP(outbuffer.buffer[1]);
	res <<= bits;
	res |= (SWAP(outbuffer.buffer[2]) >> (32 - bits)) & ((1 << (bits)) -1);
	return res;
}

void copy_output(__global hash_input* hash_input, __global ulong* hash_result, 
	inbuf inbuffer, outbuf outbuffer, int idx, int bits) {

	hash_result[idx] = get_long_from_hash(outbuffer, bits);
	hash_input[idx].buffer[0] = inbuffer.buffer[0];
	hash_input[idx].buffer[1] = inbuffer.buffer[1];
	hash_input[idx].buffer[2] = inbuffer.buffer[2];
}



__kernel void fill_hash_set(__global hash_input* hash_input, 
	__global ulong* hash_result, int loops, int bits) {

	unsigned int idx = get_global_id(0);
	inbuf inbuffer;
	outbuf outbuffer;

	for (int i = 0; i < loops; i++) {
		get_random_word(&inbuffer, idx, i);

		hash_private(inbuffer.buffer, inbuffer.length, outbuffer.buffer);
		int hash_idx = SWAP(outbuffer.buffer[0]) >> (32 - bits);
		if (hash_result[hash_idx] == 0) {
			copy_output(hash_input, hash_result, inbuffer, outbuffer, hash_idx, bits);
		}
	}
}

void save_best_solution(__global max_hash* best_solutions, 
	max_hash* best_solution, inbuf* inbuffer, hash_input* hash_str, 
	int hash_index, int index_bits, int match_bits, int thread_idx) {
	best_solution->length = index_bits + match_bits;
	best_solution->idx = hash_index;
	uint* p0 = (uint*) &(best_solution->buffer[0]);
	uint* p1 = (uint*) &(best_solution->hash_buffer[0]);
	p0[0] = inbuffer->buffer[0];
	p0[1] = inbuffer->buffer[1];
	p0[2] = inbuffer->buffer[2];

	p1[0] = hash_str->buffer[0];
	p1[1] = hash_str->buffer[1];
	p1[2] = hash_str->buffer[2];
	best_solutions[thread_idx] = *best_solution;
}

__kernel void hash_main(__global inbuf * inbuffer, __global outbuf * outbuffer)
{
	unsigned int idx = get_global_id(0);
	// unsigned int hash[32/4]={0};
	for (int i = 0; i < 10; i++) {
		inbuffer[idx].length = 4;
		inbuffer[idx].buffer[0] = ('a' << 24) | ('b' << 16) | (('c') << 8) | ('d');
		hash_global(inbuffer[idx].buffer, inbuffer[idx].length, outbuffer[idx].buffer);
		printf("%x%x%x%x%x%x%x%x\n", 
			SWAP(outbuffer[idx].buffer[0]), 
			SWAP(outbuffer[idx].buffer[1]), 
			SWAP(outbuffer[idx].buffer[2]), 
			SWAP(outbuffer[idx].buffer[3]),
			SWAP(outbuffer[idx].buffer[4]),
			SWAP(outbuffer[idx].buffer[5]),
			SWAP(outbuffer[idx].buffer[6]),
			SWAP(outbuffer[idx].buffer[7])
		);
	}
}

__kernel void hash_check(__global ulong* hash_result, 
	__global max_hash* best_solutions,
	__global hash_input* hash_inp,
	int loops, int bits, int start_idx) {

	unsigned int idx = get_global_id(0);
	unsigned int size = get_global_size(0);
	inbuf inbuffer;
	inbuffer.length = 12;
	outbuf outbuffer;
	int best_match = 0;

	max_hash best_solution;

	for (int i = 0; i < loops; i++) {
		get_random_word(&inbuffer, size + idx, start_idx + i);
		hash_private(inbuffer.buffer, inbuffer.length, outbuffer.buffer);
		int hash_idx = SWAP(outbuffer.buffer[0]) >> (32 - bits);
		ulong hash = hash_result[hash_idx];
		hash_input hash_str = hash_inp[hash_idx];

		hash_input inp = hash_inp[hash_idx];
		char* c0 = (char*) &(inp.buffer[0]);
		ulong res = get_long_from_hash(outbuffer, bits);
		while ((hash ^ res) < (1UL << (63 - best_match))) {
			if (best_match > 100) {
				printf("ERROR\n");
				break;
			}
			best_match++;
			save_best_solution(best_solutions, 
				&best_solution, &inbuffer, &hash_str,
				hash_idx, bits, best_match, idx);
			// printf("Found best match: %d (%d+%d)\n", bits + best_match, bits, best_match);
			// printf("%lx\n%lx\n", hash, res);
			// print_hash_input_word(inbuffer);
			// printf("%.12s\n", c0);
		}
	}
}