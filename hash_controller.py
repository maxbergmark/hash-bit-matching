import pyopencl as cl

class HashController:

	def __init__(self):
		self.setup_opencl()


	def setup_opencl(self):

		self.ctx = cl.create_some_context()
		self.queue = cl.CommandQueue(self.ctx, 
			properties=cl.command_queue_properties.PROFILING_ENABLE)

		self.program = cl.Program(self.ctx, 
			open("kernels/pollard_rho.cl", "r").read()).build()

		self.threads = 2**14
		self.loops = 2**19
		self.bits = 28


	def get_hash_str(self, byte_array):
		return self.get_hash(byte_array).hex()