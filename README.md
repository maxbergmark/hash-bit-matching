# Hash Bit Matching

This project was made as a personal project to find partial hash collisions in SHA256. The goal was to find two different inputs whose hashes match as well as possible, i.e. the most bits matching. 

The algorithm used is a modified Pollard Rho attack with distinguished points, an attack that is commonly used in parallel architectures to find hash collision. It is implemented using PyOpenCL to leverage GPU hashing.

## Algorithm modification

The Pollard Rho algorithm with distinguished points can be described as follows:

1. Pick a random starting point (hash input) $`x_0`$
2. Keep repeating $`x_n = H(x_{n-1})`$ until $`x_n`$ is a distinguished hash
3. Save the distinguished hash, along with metadata including the original input $`x_0`$ and the number of steps $`n`$
4. Keep repeating steps 1-3 for different random starting points until the same distinguished hash output is found twice

To learn more about it, read [this paper](http://www.cs.csi.cuny.edu/~zhangx/papers/P_2018_LISAT_Weber_Zhang.pdf) describing the article in depth. 

The Pollard Rho attack is commonly used to find hash collisions. It is not directly suited to find partial hash collsions, since the birthday attack only works for full hash collisions. But if we want to find a hash collision of $`b`$ bits, step 2 above can be changed to repeating $`x_n = H(x_{n-1}[:b])`$, i.e. only copy the first b bits of $`x_{n-1}`$ in each step. 

In general, any injective function using the first $`b`$ bits of each hash can be used: $`x_n = H(f_b(x_{n-1})`$, where `f_b` is some injective function that preserves the first $`b`$ bits of its input. As an example, here are two inputs with 80 matching bits, using an injective function that prefixes the input with the string `max_` and creates a hex string using the charset `"maxbergkMAXBERGK"`:

```
Matching bits: 80
    max_GrAMgBaegrrBGEmgaBEx -> d0f61808cede4f7720f9e9631a6e0a66f69914d5b11eb3968e55122b2e2b70c2
    max_gkKRMmEXXeERGGBbKbEX -> d0f61808cede4f7720f940ccbfe0e131dfb2a7a743ec2e5f97620a8e0a643c56
```

## Examples

All example inputs are hex encoded binary data. They can be verified using [this tool](https://emn178.github.io/online-tools/sha256.html).
```
Matching bits: 79
	312f40e65925903a9be0 -> 557672f5ed89037fe4c3e511592eb8a67aba132f3b6f466adb1970840858b477
	b4bf29c71b09d90d9e70 -> 557672f5ed89037fe4c2662aa7eede95995a660b8484d7ee03ed5782101c6084

Matching bits: 81
	c9dcdf68b90a54da7caf -> a92c2759c169a5a97cfa84b9127855aa25437406519171f976dafc9befb9c18e
	068eeccc954e7a6df277 -> a92c2759c169a5a97cfad33d34df1cfc56edc99afd44263406707bd36846fdee

Matching bits: 90
	e28d6c2e113074220d30e700 -> 47e47e0383d70d51f4895b490bc1c5d33bc34a7eff58feb1bea2db55b5a1e8be
	5541d9e14b780c350d141100 -> 47e47e0383d70d51f4895b6ffc5918a76fc34ef98b6f4d229b7883f2392b897a

Matching bits: 101
	95495df9020f2b57f2a1aaede0 -> f41b6824d3f9494b4dffd633934a50214e1ee2c1b427acbce4ecb21adcfa9997
	ce0e7ea4def8987ae249129ee0 -> f41b6824d3f9494b4dffd633953dc499bc438e9691318fceab6cb823abc51fbd
```

## Stats

Generating matches longer than 100 bits require a lot of calculation. The output below is from an older version of the program, for the 101 bit match above. 

    Kernel executions: 535
    Hashes: 1.47e+15
    Hash volume: 41.797PB
    Hash efficiency: 76.787%
    Time:  8d 23h 11m 51.2s
    Speed: 1898.25MHz
    Total distinguished points: 8.77e+07
    Distinguished points: 7.48e+07
    Maximum expected bits: 99.54
    Current probability: 39.53%
