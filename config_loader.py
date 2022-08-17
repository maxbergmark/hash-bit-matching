import yaml
import math
import os

class HashConfig(yaml.YAMLObject):

	yaml_loader = yaml.SafeLoader
	yaml_tag = "!HashConfig"

	def __init__(self, threads_exp, index_bits, search_bits, load_file, thread_limit_exp):
		self.threads_exp = threads_exp
		self.index_bits = index_bits
		self.search_bits = search_bits
		self.load_file = load_file
		self.thread_limit_exp = thread_limit_exp
		self.calculate_distinguish_bits()
		suffix = f"{self.index_bits}_{self.distinguish_bits}_{self.search_bits}"
		self.distinguished_filename = f"data/distinguished_points_{suffix}.dat"
		self.gpu_stats_filename = f"data/gpu_stats_{suffix}.dat"
		self.pickle_filename = f"data/metadata_{suffix}.pickle"

		if not os.path.isfile(self.pickle_filename):
			self.load_file = False

	@property
	def threads(self):
		return 2**self.threads_exp

	@property
	def thread_limit(self):
		return 2**self.thread_limit_exp

	@property
	def expected_d_points(self):
		return 2**(self.threads_exp 
			+ self.thread_limit_exp - self.distinguish_bits)

	def calculate_distinguish_bits(self):
		total_hashes = 2**(self.search_bits / 2)
		d_bits = math.log2(total_hashes / 2**self.index_bits)
		self.distinguish_bits = math.ceil(d_bits) + 2 + 0
		print(f"    Distinguish bits: {self.distinguish_bits}")


	@staticmethod
	def config_constructor(loader, node):
		return HashConfig(**loader.construct_mapping(node))

	@staticmethod
	def from_file(filename):

		loader = yaml.SafeLoader
		loader.add_constructor("!HashConfig", HashConfig.config_constructor)
		with open(filename, "r") as stream:
			try:
				return yaml.safe_load(stream)
			except yaml.YAMLError as e:
				print(e)


