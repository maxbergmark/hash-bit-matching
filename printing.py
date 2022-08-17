import math
from helpers import format_time

class Printer:

	def print_intro_stats(self, controller):
		if controller.config.load_file:
			n = float(controller._used_hashes)
			hash_rate = n / controller.elapsed
		else:
			n = 0
			hash_rate = 1.9e9

		d = 2**(controller.config.search_bits)
		probability = 1 - math.exp(-n**2/(2*d))
		percentiles = [0.50, 0.75, 0.90, 0.99]
		num_hashes = [(-2*d*math.log(1-p))**.5 for p in percentiles]
		expected_time = [n / hash_rate for n in num_hashes]
		remaining_time = [e - controller.elapsed for e in expected_time]

		print(f"    Current probability: {100*probability:.2f}%")
		print(f"    Expected total time ({100*percentiles[0]}%):    ", 
			f"{format_time(expected_time[0])}")
		for i, p in enumerate(percentiles):
			print(f"    Expected remaining time ({100*p:.0f}%):", 
				f"{format_time(remaining_time[i])} ({num_hashes[i]:.3e})")

	def print_end_stats(self, controller):
		hash_efficiency = float(controller.used_checks) / float(controller.total_checks)
		n = float(controller.total_checks)
		expected_bits = math.log2(-n**2/(2*math.log(1 - 0.5)))
		d = 2**(controller.config.search_bits)
		p = 1 - math.exp(-n**2/(2*d))

		print("\nStats:\n")
		print(f"    Kernel executions: {controller.i}")
		print(f"    Hashes: {controller.total_checks:.2e}")
		print(f"    Hash volume: {controller.total_checks*32/1024**5:.3f}PB")
		print(f"    Hash efficiency: {100*hash_efficiency:.3f}%")
		print(f"    Time: {format_time(controller.elapsed)}")
		print(f"    Speed: {controller.total_checks/controller.elapsed*1e-6:.2f}MHz")
		print(f"    Total distinguished points: {controller.total_d_points:.2e}")
		print(f"    Maximum expected bits: {expected_bits:.2f}")
		print(f"    Current probability: {100*p:.2f}%")