#include "kernels/printing.cl"
#include "kernels/hash_types.cl"
#include "kernels/sha256_main.cl"
#include "kernels/helpers.cl"

#define USE_TRANSFORMED 1

void check_distinguished_point(
	__global distinguished_point* distinguished_points, 
	__private outbuf* outbuffer, __private inbuf* original_input,
	const int first_offset, const int second_offset, int j, int search_bits, 
	long* unique_d_points) {
	
	uint point_idx = get_point_idx(first_offset, second_offset, outbuffer);
	__private distinguished_point private_point = distinguished_points[point_idx];

	if (private_point.offset > 0) { 
		if (hash_equal(&private_point, outbuffer)) {
			print_collision(*original_input, 
				*outbuffer, private_point, j, search_bits);
		}
	} else {
		(*unique_d_points)++;
		save_private_point(private_point, *outbuffer, 
			*original_input, distinguished_points, point_idx, j);
	}
}

void add_distinguished_point(
	__global dp_data* distinguished_points,
	volatile __global int* d_point_index,
	__private outbuf* outbuffer, __private inbuf* original_input,
	long chain_index, int i, int thread_idx
	) {

	int idx = atomic_inc(d_point_index);
	dp_data dp;
	dp.offset = i - chain_index;
	for (int j = 0; j < ceilDiv((*original_input).length, 4); j++) {
		dp.inbuffer.buffer[j] = (*original_input).buffer[j];
	}
	dp.inbuffer.length = (*original_input).length;
	for (int j = 0; j < 8; j++) {
		dp.outbuffer.buffer[j] = (*outbuffer).buffer[j];		
	}

	distinguished_points[idx] = dp;
}

__kernel void pollard_rho_check(
	__global distinguished_point* distinguished_points, 
	__global long* gpu_stats,
	int distinguish_bits, int index_bits, int offset, int search_bits) {

	int idx = get_global_id(0);
	__private inbuf inbuffer;
	__private inbuf original_input;
	__private outbuf outbuffer;

	const int first_offset = index_bits - (32 - distinguish_bits);
	const int second_offset = 32 - max(0, first_offset);

	int limit = 10 * (1 << distinguish_bits);
	uint distinguish_filter = SWAP(0xFFFFFFFF ^ (
		(1U << (32 - distinguish_bits)) - 1));
	long total_hashes = 0;
	long total_used_hashes = 0;
	long num_d_points = 0;
	long unique_d_points = 0;
	int i = 0;
	int chain_start = 0;
	uint checksum = 0;

	get_random_words(&inbuffer, &original_input, idx, i + offset);
	if (idx == 0) {
		printf("test: %d %d %d %d %d\n", 
			distinguish_bits, index_bits, offset, search_bits, limit);
	}
	if (idx == 0) {
		printf("starting with input: ");
		print_hash_input(inbuffer);
	}

	for (int j = 0; j + 1*chain_start < limit; j++) {
		hash_private(inbuffer.buffer, inbuffer.length, outbuffer.buffer);
		total_hashes++;
		checksum ^= outbuffer.buffer[0];

		if ((outbuffer.buffer[0] & distinguish_filter) == 0) {
			total_used_hashes = total_hashes;
			num_d_points++;
			chain_start += j;
			i++;
			j = 0;
			get_random_words(&inbuffer, &original_input, idx, i + offset);
		} else {
			copy_n_bits(&inbuffer, &outbuffer, search_bits);
		}
	}

	if (idx == 0) {
		printf("checksum: %08x\n", checksum);
		printf("%08x\n", distinguish_filter);
		if (checksum != 0xb55b0d13) {
			printf("\n\n\n\nERROR!!!!\n\n\n\n\n\n");
		}
	}

	gpu_stats[4*idx] += total_hashes;
	gpu_stats[4*idx+1] += num_d_points;
	gpu_stats[4*idx+2] += total_used_hashes;
	gpu_stats[4*idx+3] += unique_d_points;
}

__kernel void pollard_rho_effective(
	__global dp_data* distinguished_points,
	__global gpu_stats* gpu_stats_array,
	volatile __global int* d_point_index,
	int distinguish_bits, int search_bits, const int limit) {

	int idx = get_global_id(0);
	__private inbuf inbuffer;
	__private inbuf original_input;
	__private outbuf outbuffer;
	const uint distinguish_filter = SWAP(0xFFFFFFFF ^ (
		(1U << (32 - distinguish_bits)) - 1));
	const char tokens[16] = "MAXBERGKmaxbergk";

	__private gpu_stats private_stats = gpu_stats_array[idx];

	if (private_stats.total_hashes == 0) {
		get_random_words(&inbuffer, &original_input, idx, 0);
	} else {
		original_input = private_stats.original_input;
		inbuffer = private_stats.current_hash;
	}

	for (int i = 0; i < limit; i++) {
		hash_private(inbuffer.buffer, inbuffer.length, outbuffer.buffer);
		if ((outbuffer.buffer[0] & distinguish_filter) == 0) {
			if (outbuffer.buffer[0] == SWAP(0x0304ea0f)) {
				//f144c016b2cd1d14d96aa285d777f1dcb78bbd74f3c799c1536117b9
				printf("\n\nfound hash: %ld, %d, %d, %.12s\n\n", 
					private_stats.chain_index, i, idx, original_input.buffer);
			}

			add_distinguished_point(distinguished_points, d_point_index, 
				&outbuffer, &original_input, private_stats.chain_index, i, idx);
			private_stats.start_index++;
			private_stats.chain_index = i+1;
			private_stats.used_hashes = private_stats.total_hashes + i;
			get_random_words(&inbuffer, &original_input, 
				idx, private_stats.start_index);

		} else {
#ifdef USE_TRANSFORMED
			copy_n_bits_transformed(&inbuffer, &outbuffer, tokens, search_bits);
#else
			copy_n_bits(&inbuffer, &outbuffer, search_bits);
#endif
		}
		
	}

	private_stats.current_hash = inbuffer;
	private_stats.original_input = original_input;		
	private_stats.total_hashes += limit;
	private_stats.chain_index -= limit;
	gpu_stats_array[idx] = private_stats;
}

__kernel void verify(__global dp_data* points, 
	int distinguish_bits, int search_bits) {

	const uint distinguish_filter = SWAP(0xFFFFFFFF ^ (
		(1U << (32 - distinguish_bits)) - 1));
	const char tokens[16] = "MAXBERGKmaxbergk";

	__private dp_data dp0 = points[0];
	__private dp_data dp1 = points[1];
	__private inbuf i0 = dp0.inbuffer;
	__private inbuf i1 = dp1.inbuffer;
	__private outbuf o0;
	__private outbuf o1;
	int offset0 = dp0.offset;
	int offset1 = dp1.offset;

	for (int i = 0; i < max(0, offset0 - offset1); i++) {
		hash_private(i0.buffer, i0.length, o0.buffer);
#ifdef USE_TRANSFORMED
		copy_n_bits_transformed(&i0, &o0, tokens, search_bits);
#else
		copy_n_bits(&i0, &o0, search_bits);
#endif
	}

	for (int i = 0; i < max(0, offset1 - offset0); i++) {
		hash_private(i1.buffer, i1.length, o1.buffer);
#ifdef USE_TRANSFORMED
		copy_n_bits_transformed(&i1, &o1, tokens, search_bits);
#else
		copy_n_bits(&i1, &o1, search_bits);
#endif
	}

	for (int i = 0; i < min(offset0, offset1); i++) {
		hash_private(i0.buffer, i0.length, o0.buffer);
		hash_private(i1.buffer, i1.length, o1.buffer);

		if (o0.buffer[0] == o1.buffer[0]) {
			printf("Found match:\n");
			int matching_bits = get_matching_bits(o0, o1);
			printf("    Matching bits: %d\n    ", matching_bits);
			for (int j = 0; j < ceilDiv(i0.length, 4); j++) {
#ifdef USE_TRANSFORMED
				printf("%.4s", (char*) &i0.buffer[j]);
#else
				printf("%08x", SWAP(i0.buffer[j]));
#endif
			}
			printf(" (%d) -> ", i0.length);
			print_hash_match(o0, matching_bits);
			printf("    ");
			for (int j = 0; j < ceilDiv(i1.length, 4); j++) {
#ifdef USE_TRANSFORMED
				printf("%.4s", (char*) &i1.buffer[j]);
#else
				printf("%08x", SWAP(i1.buffer[j]));
#endif
			}
			printf(" (%d) -> ", i1.length);
			print_hash_match(o1, matching_bits);
			printf("\n");
			return;

		}

#ifdef USE_TRANSFORMED
		copy_n_bits_transformed(&i0, &o0, tokens, search_bits);
		copy_n_bits_transformed(&i1, &o1, tokens, search_bits);
#else
		copy_n_bits(&i0, &o0, search_bits);
		copy_n_bits(&i1, &o1, search_bits);
#endif
	}
}
