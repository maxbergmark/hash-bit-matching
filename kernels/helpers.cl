#pragma once

void get_random_word(inbuf* inbuffer, int idx, int i) {
	inbuffer->length = 12;
	inbuffer->buffer[0] = 0;
	inbuffer->buffer[1] = 0;
	inbuffer->buffer[2] = 0;
	for (int j = 0; j < 4; j++) {
		inbuffer->buffer[0] <<= 8;
		inbuffer->buffer[0] |= 'a' + (i % 16);
		i /= 16;
		inbuffer->buffer[1] <<= 8;
		inbuffer->buffer[1] |= 'a' + (i % 16);
		i /= 16;
		inbuffer->buffer[2] <<= 8;
		inbuffer->buffer[2] |= 'a' + (idx % 16);
		idx /= 16;
	}
}

void get_random_words(inbuf* inbuffer, inbuf* original_input, int idx, int i) {
	get_random_word(original_input, idx, i);
	inbuffer->buffer[0] = original_input->buffer[0];
	inbuffer->buffer[1] = original_input->buffer[1];
	inbuffer->buffer[2] = original_input->buffer[2];
	inbuffer->length = original_input->length;

}

void copy_n_bits(__private inbuf* inbuffer, __private outbuf* outbuffer, int bits) {
	int idx = 0;
	inbuffer->length = ceilDiv(bits, 8);
	while (bits >= 32) {
		inbuffer->buffer[idx] = outbuffer->buffer[idx];
		idx++;
		bits -= 32;
	}
	uint mask = ((1 << bits) - 1) << (32 - bits);
	inbuffer->buffer[idx] = SWAP(SWAP(outbuffer->buffer[idx]) & mask);
}

void copy_n_bits_transformed(__private inbuf* inbuffer, __private const outbuf* outbuffer, const char* tokens, int bits) {
//	const char tokens[16] = "MAXBERGKmaxbergk";
//	char ct[4];
//	int idx = 0;
	inbuffer->length = ceilDiv(bits, 4);
	unsigned char* frombuf = (unsigned char*) outbuffer->buffer;
	char* tobuf = (unsigned char*) inbuffer->buffer;

	while (bits >= 8) {
		*tobuf++ = tokens[(*frombuf>>4) & 0xF];
		*tobuf++ = tokens[(*frombuf++) & 0xF];
		bits -= 8;
	}
}

bool hash_equal(distinguished_point* private_point, outbuf* outbuffer) {
	return private_point->half_hash[0] == outbuffer->buffer[0]
		& private_point->half_hash[1] == outbuffer->buffer[1]
		& private_point->half_hash[2] == outbuffer->buffer[2]
		& private_point->half_hash[3] == outbuffer->buffer[3];
}

void save_private_point(distinguished_point private_point, outbuf outbuffer, inbuf original_input, 
	__global distinguished_point* distinguished_points, uint point_idx, int j) {

	private_point.offset = j;
	word* ptr = (word*) private_point.hash_input;
	ptr[0] = original_input.buffer[0];
	ptr[1] = original_input.buffer[1];
	ptr[2] = original_input.buffer[2];
	private_point.half_hash[0] = outbuffer.buffer[0];
	private_point.half_hash[1] = outbuffer.buffer[1];
	private_point.half_hash[2] = outbuffer.buffer[2];
	private_point.half_hash[3] = outbuffer.buffer[3];

	distinguished_points[point_idx] = private_point;
}

uint get_point_idx(int first_offset, int second_offset, outbuf* outbuffer) {
	return (first_offset >= 0 ? SWAP(outbuffer->buffer[0]) << first_offset : SWAP(outbuffer->buffer[0]) >> -first_offset)
		| (second_offset < 32 ? SWAP(outbuffer->buffer[1]) >> second_offset : 0);
}
