import numpy as np
import pyopencl as cl

def print_d_point(d_point):
	l = d_point["inbuffer"]["length"]
	offset = d_point["offset"]
	print(f"Data ({l}, {offset}):", 
		d_point["inbuffer"]["buffer"].tobytes()[:l].hex(),
		d_point["inbuffer"]["buffer"].tobytes()[:l].decode("utf8")
	)


class CollisionChecker:

	def __init__(self, config, ctx, program, queue):
		self.distinguished_point_set = {}
		self.config = config
		self.ctx = ctx
		self.program = program
		self.queue = queue

	@property
	def num_dp(self):
		return len(self.distinguished_point_set)

	def set_distinguished_point_set(self, dp_set):
		self.distinguished_point_set = dp_set

	def check_distinguished_points(self, distinguished_points, n):
		for i in range(n):
			b = distinguished_points[i]["outbuffer"]["buffer"].tobytes().hex()
			if b in self.distinguished_point_set:
				# print("\nmatch found!")
				# print("points:", len(self.distinguished_point_set))
				# print_d_point(distinguished_points[i])
				# print_d_point(self.distinguished_point_set[b])
				self.verify(distinguished_points[i], 
					self.distinguished_point_set[b], self.config.search_bits)
			else:
				self.distinguished_point_set[b] = distinguished_points[i].copy()

	def verify(self, dp_0, dp_1, bits):
		l = dp_0["inbuffer"]["length"]
		o_0, o_1 = int(dp_0["offset"]), int(dp_1["offset"])
		s_0 = dp_0["inbuffer"]["buffer"].tobytes()[:l].decode("utf8")
		s_1 = dp_1["inbuffer"]["buffer"].tobytes()[:l].decode("utf8")
		print(f"\nself.verify(\"{s_0}\", {o_0}, \"{s_1}\", {o_1}, {bits})")
		dp_np = np.array([dp_0, dp_1])
		mf = cl.mem_flags
		dp_g = cl.Buffer(self.ctx, 
			mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=dp_np)
		self.program.verify(self.queue, (1,), None, 
			dp_g, 
			np.int32(self.config.distinguish_bits),
			np.int32(self.config.search_bits)
		)
		quit()