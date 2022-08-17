import math
import pyopencl as cl
import os
import pickle
import numpy as np
import time

from multi_buffer import MultiBuffer
from hash_controller import HashController
from verifier import Verifier
from config_loader import HashConfig
from collision_checker import CollisionChecker
from printing import Printer
from data_loader import DataLoader



class PollardRhoController(HashController):

	def __init__(self):
		super().__init__()

		print("\nIntro stats:")
		self.verifier = Verifier()
		self.printer = Printer()
		self.config = HashConfig.from_file("config.yaml")
		self.data_loader = DataLoader(self.config, self)
		self.collision_checker = CollisionChecker(self.config, 
			self.ctx, self.program, self.queue)

		self.data_loader.get_metadata()
		self.printer.print_intro_stats(self)

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


	def call_kernel(self):
		self.program.pollard_rho_effective(
			self.queue, (self.config.threads,), None, 
			self.distinguished_points.gpu_buffer, 
			self.gpu_stats.gpu_buffer, 
			self.d_point_index.gpu_buffer,
			np.int32(self.config.distinguish_bits), 
			np.int32(self.config.search_bits),
			np.int32(self.config.thread_limit)
		)

	def prepare(self):
		temp_elapsed = self.elapsed + time.perf_counter() - self.start_time
		print((f"\rRunning kernel: {self.i+1:8d} "
			f"({self.collision_checker.num_dp:9d}, "
			f"{100*float(self.probability):.2f}%), "
			f"{1e-6*(self.total_checks / temp_elapsed):.0f}MHz"), end="")
		self.d_point_index[0] = 0
		self.d_point_index.to_gpu()

	def copy_and_check(self):
		self.distinguished_points.from_gpu()
		self.d_point_index.from_gpu()
		self.gpu_stats.from_gpu()
		self.queue.finish()

		self.collision_checker.check_distinguished_points(
			self.distinguished_points, 
			self.d_point_index[0])

	def run(self):
		while True:
			self.prepare()
			self.call_kernel()
			self.copy_and_check()
			self.i += 1

	def pollard_rho(self):
		print("\nStarting Pollard's rho attack")
		self.data_loader.create_buffers()
		self.start_time = time.perf_counter()
		try:
			self.run()
		except KeyboardInterrupt:
			print("\r" + " "*80)
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
		self.printer.print_end_stats(self)
		self.data_loader.save_result()