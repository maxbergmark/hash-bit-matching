import pyopencl as cl
import numpy as np

class MultiBuffer:

	def __init__(self, ctx, queue, *, dtype, size=None, 
		memflags = cl.mem_flags.READ_WRITE):
		
		self.queue = queue
		self.ctx = ctx
		self.dtype = dtype
		if size is not None:
			self.size = size
			self.numpy_buffer = np.zeros(size, dtype=dtype)
			self.gpu_buffer = cl.Buffer(self.ctx, memflags, 
				size=self.numpy_buffer.nbytes)
			self.to_gpu()

	def __getitem__(self, idx):
		return self.numpy_buffer[idx]

	def __setitem__(self, idx, value):
		self.numpy_buffer[idx] = value

	def to_gpu(self):
		cl.enqueue_copy(self.queue, self.gpu_buffer, self.numpy_buffer)

	def from_gpu(self):
		cl.enqueue_copy(self.queue, self.numpy_buffer, self.gpu_buffer)

	@staticmethod
	def fromfile(filename, ctx, queue, dtype, memflags = cl.mem_flags.READ_WRITE):
		b = MultiBuffer(ctx, queue, dtype=dtype)
		b.numpy_buffer = np.fromfile(filename, dtype=dtype)
		b.gpu_buffer = cl.Buffer(ctx, memflags, size=b.numpy_buffer.nbytes)
		b.to_gpu()
		return b

	def tofile(self, filename):
		self.numpy_buffer.tofile(filename)