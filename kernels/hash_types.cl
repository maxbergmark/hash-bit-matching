#pragma once

/*
	In- and out- buffer structures (of int32), with variable sizes, for hashing.
	These allow indexing just using just get_global_id(0)
	Variables tagged with <..> are replaced, so we can specify just enough room for the data.
	These are:
		- hashBlockSize_bits   : The hash's block size in Bits
		- inMaxNumBlocks	  : per hash operation
		- hashDigestSize_bits   : The hash's digest size in Bits

	Originally adapted from Bjorn Kerler's sha256.cl
	MIT License
*/

#define DEBUG 0

// ========== Debugging function ============

#ifdef DEBUG
#if DEBUG

	#define def_printFromWord(tag, funcName, end)			   \
	/* For printing the string of bytes stored in an array of words.
	Option to print hex. */	\
	static void funcName(tag const word *arr, const unsigned int len_bytes, const bool hex)\
	{										   \
		for (int j = 0; j < len_bytes; j++){	\
			word v = arr[j / wordSize];				 \
			word r = mod(j,wordSize) * 8;				\
			/* Prints little endian, since that's what we use */   \
			v = (v >> r) & 0xFF;				\
			if (hex) {						  \
				printf("%02x", v);			  \
			} else {							\
				printf("%c", (char)v);		  \
			}								   \
		}									   \
		printf(end);							\
	}

	def_printFromWord(__private, printFromWord, "")
	def_printFromWord(__global, printFromWord_glbl, "")
	def_printFromWord(__private, printFromWord_n, "\n")
	def_printFromWord(__global, printFromWord_glbl_n, "\n")

#endif
#endif

// All macros left defined for usage in the program
#define ceilDiv(n,d) (((n) + (d) - 1) / (d))

// All important now, defining whether we're working with unsigned ints or longs
#define wordSize 4

// Practical sizes of buffers, in words.
#define inBufferSize ceilDiv(128, wordSize)
#define outBufferSize ceilDiv(32, wordSize)
#define saltBufferSize ceilDiv(32, wordSize)
#define ctBufferSize ceilDiv(0, wordSize)

// 
#define hashBlockSize_bytes ceilDiv(512, 8) /* Needs to be a multiple of 4, or 8 when we work with unsigned longs */
#define hashDigestSize_bytes ceilDiv(256, 8)

// just Size always implies _word
#define hashBlockSize ceilDiv(hashBlockSize_bytes, wordSize)
#define hashDigestSize ceilDiv(hashDigestSize_bytes, wordSize)


// Ultimately hoping to faze out the Size_int32/long64,
//   in favour of just size (_word implied)

#define hashBlockSize_int32 hashBlockSize
#define hashDigestSize_int32 hashDigestSize
#define word unsigned int

#define BYTE_TO_BINARY_PATTERN "%c%c%c%c%c%c%c%c"
#define BYTE_TO_BINARY(byte)  \
  (byte & 0x80 ? '1' : '0'), \
  (byte & 0x40 ? '1' : '0'), \
  (byte & 0x20 ? '1' : '0'), \
  (byte & 0x10 ? '1' : '0'), \
  (byte & 0x08 ? '1' : '0'), \
  (byte & 0x04 ? '1' : '0'), \
  (byte & 0x02 ? '1' : '0'), \
  (byte & 0x01 ? '1' : '0') 

	
unsigned int SWAP (unsigned int val)
{
	return (rotate(((val) & 0x00FF00FF), 24U) | rotate(((val) & 0xFF00FF00), 8U));
}





// ====  Define the structs with the right word size  =====
//  Helpful & more cohesive to have the lengths of structures as words too,
//   (rather than unsigned int for both)
typedef struct {
	word length; // in bytes
	word buffer[inBufferSize];
} inbuf;

typedef struct {
	word buffer[outBufferSize];
} outbuf;

typedef struct {
	uint buffer[3];
} hash_input;

typedef struct {
	int idx;
	int length;
	uchar buffer[12];
	uchar hash_buffer[12];
} max_hash;

typedef struct {
	uint offset;
	uchar hash_input[12];
	word half_hash[outBufferSize / 2];
} distinguished_point;

typedef struct {
	uint offset;
	inbuf inbuffer;
	outbuf outbuffer;
} dp_data;

// Salt buffer, used by pbkdf2 & pbe
typedef struct {
	word length; // in bytes
	word buffer[saltBufferSize];
} saltbuf;

// ciphertext buffer, used in pbe.
// no code relating to this in the opencl.py core, dealt with in signal_pbe_mac.cl as it's a special case
typedef struct {
	word length; // in bytes
	word buffer[ctBufferSize];
} ctbuf;

typedef struct {
	inbuf current_hash;
	inbuf original_input;
	long start_index;
	long chain_index;
	long total_hashes;
	long used_hashes;
} gpu_stats;

