import math
import pyopencl as cl
import os
import pickle
import numpy as np
import time

from multi_buffer import MultiBuffer
from hash_controller import HashController
from helpers import format_time
from verifier import Verifier
from config_loader import HashConfig
from collision_checker import CollisionChecker
from data_types import (gpu_stats_dtype, 
	inbuf_dtype, outbuf_dtype, dp_data_dtype)


class PollardRhoController(HashController):

	def __init__(self):
		super().__init__()

		print("\nIntro stats:")
		self.verifier = Verifier()
		self.config = HashConfig.from_file("config.yaml")
		self.collision_checker = CollisionChecker(self.config, 
			self.ctx, self.program, self.queue)

		self.get_metadata()
		self.print_intro_stats()

	@property
	def total_checks(self):
		return self.gpu_stats[:]["total_hashes"].sum()

	@property
	def used_checks(self):
		return self.gpu_stats[:]["used_hashes"].sum()
		
	@property
	def total_d_points(self):
		return self.gpu_stats[:]["start_index"].sum()

	@property
	def probability(self):
		d = 2**(self.config.search_bits)
		n = float(self.used_checks)
		return 1 - math.exp(-n**2/(2*d))


	def print_intro_stats(self):
		if self.config.load_file:
			n = float(self._used_hashes)
			hash_rate = n / self.elapsed
		else:
			n = 0
			hash_rate = 1.9e9

		d = 2**(self.config.search_bits)
		probability = 1 - math.exp(-n**2/(2*d))
		percentiles = [0.50, 0.75, 0.90, 0.99]
		num_hashes = [(-2*d*math.log(1-p))**.5 for p in percentiles]
		expected_time = [n / hash_rate for n in num_hashes]
		remaining_time = [e - self.elapsed for e in expected_time]

		print(f"    Current probability: {100*probability:.2f}%")
		print(f"    Expected total time ({100*percentiles[0]}%):    ", 
			f"{format_time(expected_time[0])}")
		for i, p in enumerate(percentiles):
			print(f"    Expected remaining time ({100*p:.0f}%):", 
				f"{format_time(remaining_time[i])} ({num_hashes[i]:.3e})")

	def create_buffers(self):

		self.create_dp_data()
		self.create_gpu_stats()
		self.d_point_index = MultiBuffer(
			self.ctx, self.queue, 
			size=1, dtype=np.int32
		)

	def create_dp_data(self):

		self.distinguished_points = MultiBuffer(
			self.ctx, self.queue, 
			size=10*self.config.expected_d_points, dtype=dp_data_dtype
		)

	def create_gpu_stats(self):

		if self.config.load_file:
			self.gpu_stats = MultiBuffer.fromfile(
				self.config.gpu_stats_filename, 
				self.ctx, self.queue, gpu_stats_dtype
			)
		else:
			self.gpu_stats = MultiBuffer(
				self.ctx, self.queue, 
				size=self.threads, dtype=gpu_stats_dtype
			)

	def get_metadata(self):
		if self.config.load_file:
			with open(self.config.pickle_filename, "rb") as f:
				d = pickle.load(f)
				self.i = d["i"]
				self.elapsed = d["elapsed"]
				self._total_hashes = d["total_hashes"]
				self._used_hashes = d["used_hashes"]
				self._total_d_points = d["total_d_points"]
				self.collision_checker.set_distinguished_point_set(
					d["distinguished_points"])
		else:
			self.i = 0
			self.elapsed = 0
			self._total_hashes = 0
			self._used_hashes = 0
			self._total_d_points = 0


	def call_kernel(self):
		self.program.pollard_rho_effective(
			self.queue, (self.threads,), None, 
			self.distinguished_points.gpu_buffer, 
			self.gpu_stats.gpu_buffer, 
			self.d_point_index.gpu_buffer,
			np.int32(self.config.distinguish_bits), 
			np.int32(self.config.search_bits),
			np.int32(self.config.thread_limit)
		)

	def run(self):
		# self.program.verify(self.queue, (1,), None)
		# quit()
		while True:
			temp_elapsed = self.elapsed + time.perf_counter() - self.start_time
			print((f"\rRunning kernel: {self.i+1:8d} "
				f"({self.collision_checker.num_dp:9d}, "
				f"{100*float(self.probability):.2f}%), "
				f"{1e-6*(self.total_checks / temp_elapsed):.0f}MHz"), end="")
			self.d_point_index[0] = 0
			self.d_point_index.to_gpu()
			# t0 = time.perf_counter()
			self.call_kernel()
			# self.queue.finish()
			# t1 = time.perf_counter()
			# print("\n", self.threads * self.thread_limit / (t1-t0))

			self.distinguished_points.from_gpu()
			self.d_point_index.from_gpu()
			self.gpu_stats.from_gpu()
			self.queue.finish()
			self.collision_checker.check_distinguished_points(
				self.distinguished_points, 
				self.d_point_index[0])

			self.i += 1

	def print_end_stats(self):
		hash_efficiency = float(self.used_checks) / float(self.total_checks)
		n = float(self.total_checks)
		expected_bits = math.log2(-n**2/(2*math.log(1 - 0.5)))
		d = 2**(self.config.search_bits)
		p = 1 - math.exp(-n**2/(2*d))

		print("\nStats:\n")
		print(f"    Kernel executions: {self.i}")
		print(f"    Hashes: {self.total_checks:.2e}")
		print(f"    Hash volume: {self.total_checks*32/1024**5:.3f}PB")
		print(f"    Hash efficiency: {100*hash_efficiency:.3f}%")
		print(f"    Time: {format_time(self.elapsed)}")
		print(f"    Speed: {self.total_checks/self.elapsed*1e-6:.2f}MHz")
		print(f"    Total distinguished points: {self.total_d_points:.2e}")
		print(f"    Maximum expected bits: {expected_bits:.2f}")
		print(f"    Current probability: {100*p:.2f}%")

	def save_result(self):
		print("\nSaving data...", end="\t", flush=True)
		self.gpu_stats.tofile(self.config.gpu_stats_filename)
		with open(self.config.pickle_filename, "wb") as f:
			d = {
				"i": self.i, 
				"elapsed": self.elapsed, 
				"total_hashes": self.total_checks,
				"used_hashes": self.used_checks,
				"total_d_points": self.total_d_points,
				"distinguished_points": self.collision_checker.distinguished_point_set
			}
			pickle.dump(d, f)
		print("Saved!")

	def pollard_rho(self):
		print("\nStarting Pollard's rho attack")
		self.create_buffers()
		self.start_time = time.perf_counter()
		try:
			self.run()
		except KeyboardInterrupt:
			print("\r" + " "*40)
			print("Exiting program")
			self.i += 1

		self.queue.finish()
		t1 = time.perf_counter()
		self.elapsed += t1-self.start_time

		print("\r" + " "*80)
		print("Kernel finished!")
		print("Copying buffers from GPU...", end="\t", flush=True)
		self.distinguished_points.from_gpu()
		self.gpu_stats.from_gpu()
		self.queue.finish()
		print("Done!")
		self.print_end_stats()
		self.save_result()