import numpy as np
import pickle

from multi_buffer import MultiBuffer
from data_types import (gpu_stats_dtype, 
	inbuf_dtype, outbuf_dtype, dp_data_dtype)

class DataLoader:

	def __init__(self, config, controller):
		self.config = config
		self.controller = controller

	def save_result(self):
		print("\nSaving data...", end="\t", flush=True)
		self.controller.gpu_stats.tofile(self.config.gpu_stats_filename)
		with open(self.config.pickle_filename, "wb") as f:
			d = {
				"i": self.controller.i, 
				"elapsed": self.controller.elapsed, 
				"total_hashes": self.controller.total_checks,
				"used_hashes": self.controller.used_checks,
				"total_d_points": self.controller.total_d_points,
				"distinguished_points": 
					self.controller.collision_checker.distinguished_point_set
			}
			pickle.dump(d, f)
		print("Saved!")

	def create_buffers(self):

		self.create_dp_data()
		self.create_gpu_stats()
		self.controller.d_point_index = MultiBuffer(
			self.controller.ctx, self.controller.queue, 
			size=1, dtype=np.int32
		)

	def create_dp_data(self):
		self.controller.distinguished_points = MultiBuffer(
			self.controller.ctx, self.controller.queue, 
			size=10*self.config.expected_d_points, dtype=dp_data_dtype
		)

	def create_gpu_stats(self):

		if self.config.load_file:
			self.controller.gpu_stats = MultiBuffer.fromfile(
				self.config.gpu_stats_filename, 
				self.controller.ctx, self.controller.queue, gpu_stats_dtype
			)
		else:
			self.controller.gpu_stats = MultiBuffer(
				self.controller.ctx, self.controller.queue, 
				size=self.config.threads, dtype=gpu_stats_dtype
			)

	def get_metadata(self):
		if self.config.load_file:
			with open(self.config.pickle_filename, "rb") as f:
				d = pickle.load(f)
				self.controller.i = d["i"]
				self.controller.elapsed = d["elapsed"]
				self.controller._total_hashes = d["total_hashes"]
				self.controller._used_hashes = d["used_hashes"]
				self.controller._total_d_points = d["total_d_points"]
				self.controller.collision_checker.set_distinguished_point_set(
					d["distinguished_points"])
		else:
			self.controller.i = 0
			self.controller.elapsed = 0
			self.controller._total_hashes = 0
			self.controller._used_hashes = 0
			self.controller._total_d_points = 0