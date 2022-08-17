import hashlib

from helpers import ceildiv

class Verifier:

	def __init__(self):
		pass

	def get_hash(self, byte_array):
		m = hashlib.sha256()
		m.update(byte_array)
		return bytearray(m.digest())

	def get_matching_bits(self, h0, h1):
		bits = 0
		i = 0
		while h0[i] == h1[i]:
			bits += 8
			i += 1

		j = 7
		while j >= 0 and (h0[i] & (1<<j) == h1[i] & (1<<j)):
			bits += 1
			j -= 1

		return bits

	def verify(self, input_0, length_0, input_1, length_1, matching_bits):
		matching_bytes = ceildiv(matching_bits, 8)
		remaining_bits = matching_bits - 8*(matching_bits // 8)
		b0 = bytearray(input_0.encode("utf-8"))
		b1 = bytearray(input_1.encode("utf-8"))

		if remaining_bits > 0:
			mask = ((1 << remaining_bits) - 1) << (8 - remaining_bits)
		else:
			mask = 0b11111111
		
		for i in range(max(0, length_0 - length_1)):
			b0 = self.get_hash(b0)[:matching_bytes]
			b0[-1] = b0[-1] & mask
		
		for i in range(max(0, length_1 - length_0)):
			b1 = self.get_hash(b1)[:matching_bytes]
			b1[-1] = b1[-1] & mask

		for i in range(min(length_0, length_1)):
			b0_new = self.get_hash(b0)[:matching_bytes]
			b1_new = self.get_hash(b1)[:matching_bytes]
			b0_new[-1] = b0_new[-1] & mask
			b1_new[-1] = b1_new[-1] & mask
			if (b0_new == b1_new):
				h0 = self.get_hash(b0)
				h1 = self.get_hash(b1)
				print("\nFound match:")
				print(f"    Minimum matching bits: {matching_bits}")
				print(f"    Matching bits: {self.get_matching_bits(h0, h1)}")
				print(f"    {b0.hex()} -> {h0.hex()}")
				print(f"    {b1.hex()} -> {h1.hex()}")
				return
			b0, b1 = b0_new, b1_new
			# print(b0.hex(), b1.hex())

		print("No match found")
		# print(b0.hex())
		# print(b1.hex())

	def verify_single(self, input_0, length_0, output):
		b = bytearray(input_0.encode("utf-8"))
		for i in range(length_0+1000):
			b = self.get_hash(b)[:10]
			if b.hex()[:10] == output[:10]:
				print("match:", b.hex(), i)
		# print(b.hex())

	def verify_solutions(self):

		# self.verify("aaaaaaaadpck", 10, "aaaaaaaaajic", 17, 32)
		# self.verify("aaadaaabdape", 466419, "aaakaaaadjgl", 134734, 72)
		# self.verify("aaakaaabclgj", 288819, "aaaeaaabajdb", 285067, 72)
		# self.verify("aaabaaacbdoh", 686604, "aaacaaacdjkp", 130447, 72)
		self.verify("aaaoaaaaddpj", 12361024, "aaaaaaaadhkn", 10783172+1, 80)

		return
		self.verify("ahbhaakcdejo", 2226,
			"ahbdaakcanpp", 4886, 66)
		self.verify("adnaaaafckpn", 180015,
			"adnjaaaeddoh", 361105, 72)
		self.verify("adhfahpibkno", 9581,
			"alhjabhedhhi", 7094, 76)
		self.verify("ikljamkodojc", 15719,
			"hogjamombjhc", 14501, 80)
		self.verify("fombbjfoajjh", 75324,
			"nmcaaifkbhbj", 52477, 84)
		self.verify("kjobbdnacfgg", 214049,
			"flaabaoodgjh", 122568, 84)
		self.verify("cbkgabhobkhg", 286315,
			"baggaokoabak", 97181, 84)
		self.verify("bnifahhgbmma", 26978, 
			"bdgiaagkbpai", 149203, 90)
		self.verify("danhabeecaok", 34155734, 
			"ablkanakdfmj", 17642060, 100)