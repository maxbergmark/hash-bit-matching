import pyopencl as cl
import numpy as np
import hashlib
import pickle
import math
import time
import os


from pollard_rho import PollardRhoController
from verifier import Verifier

if __name__ == "__main__":
	verifier = Verifier()
	# verifier.verify_single("aaaaaaaadhkn", 10783172, "000001014cd432d6fb0812b0")
	# verifier.verify_single("aaaoaaaaddpj", 12361024, "000001014cd432d6fb0812b0")
	# verifier.verify_solutions()
	controller = PollardRhoController()
	controller.pollard_rho()


