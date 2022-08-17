import numpy as np

inbuf_dtype = np.dtype([
	("length", np.uint32),
	("buffer", "32u4")
])

gpu_stats_dtype = np.dtype([
	("current_hash", inbuf_dtype),
	("original_input", inbuf_dtype),
	("start_index", np.int64),
	("chain_index", np.int64),
	("total_hashes", np.int64),
	("used_hashes", np.int64)
])


outbuf_dtype = np.dtype([
	("buffer", "8u4")
])

dp_data_dtype = np.dtype([
	("offset", np.uint32),
	("inbuffer", inbuf_dtype),
	("outbuffer", outbuf_dtype)
])