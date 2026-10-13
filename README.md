# BTC-fast-filter

BTC fast filter uses a bloom filter to accumulate address for fast filtering of potential bitcoin addresses on chain or in the UTXO set. The objectives are 1) compression (~50x) of data, 2) prevent overloading public API's with requests.
The tool consists of two scripts:

**1_build_bloom_filter.py** - compresses millions of addresses (2.8 GB) into ~60 MB while enabling ultra-fast membership queries (~1 µs per address). Perfect for filtering spam/scam addresses, wallet recovery, and pre-screening before API queries. The costs of using a filter instead of raw data is faster scanning but a ~1% false positive rate.

**2_verify_bloom_filter.py** - loads the bloom filter and filters input addresses (~1 µs per address) and prints them to STDOUT where they can be used to query public API's.

## Quick Start

### 1. Build Bloom filter from address list bash # From file (50M addresses, 1% false positive rate) - skip if you want to use prebuild filter
=> build the filter youserlf with the latest UTXO address snapshot from https://blockchair.com/dumps (select `Bitcoin / addresses`) 

**From STDIN (pipe)**

`cat addresses.txt | python 1_build_bloom_filter.py -o address_filter.bf`

### 2. Verify addresses (prints only matches to STDOUT)

`cat check_addresses.txt | python 2_verify_bloom_filter.py -f address_filter.bf -w 16 > matches.txt`

**Single address test**

`echo "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq" | python 2_verify_bloom_filter.py -f address_filter.bf`

---

## Installation

**Zero dependencies!** Pure Python 3.8+ with standard libraries only.

`git clone https://github.com/niels-wallet-recovery-nl/btc-fast-filter.git`

**Requirements**: Python 3.8+, 8+ GB RAM (for large builds), SSD recommended.

---

## Scripts Overview

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| **`1_build_bloom_filter.py`** | Build filter from address list | TSV/text file, STDIN | `.bf` filter file |
| **`2_verify_bloom_filter.py`** | Filter addresses against filter | STDIN addresses | Matches to STDOUT |

---

## Performance Metrics

### Build Performance (50M addresses)

| Metric | Value | Notes |
| --- | --- | --- |
| **Filter size** | ~80 MB (@ 1% FP) | Adjustable |
| **Build time** | ~10-30 min | Depends on CPU/RAM |
| **Throughput** | ~50K-100K/sec | Addresses processed |
| **Memory** | ~80-120 MB | During build |

### Verification Performance

| Metric | Value | Notes |
| --- | --- | --- |
| **Single address** | ~1-2 µs | Extremely fast |
| **Parallel (16 cores)** | ~16 ms for 50K addresses | Near-instant |
| **False positives** | ~1% (tunable) | Configurable |
| **False negatives** | 0%  | Never miss a real match |

---

## Configuration

### Tune False Positive Rate

| FP Rate | Size (50M items) | Use Case |
| --- | --- | --- |
| **0.1%** | ~240 MB | Critical filtering (no tolerance for FP) |
| **1%** | ~80 MB | ✅ Default (balanced) |
| **10%** | ~25 MB | Quick spam/scam filter |

---

## Bloom Filter vs. BBF RSA Accumulator

| Feature | Bloom Filter | BBF RSA Accumulator |
| --- | --- | --- |
| **Storage (50M)** | ~80 MB | ~100 MB |
| **Verification speed** | ~1 µs/addr | ~16 ms/addr |
| **False positives** | Yes (1%) | None |
| **False negatives** | None | None |
| **Security** | Probabilistic | Cryptographic |
| **Complexity** | Low (hashing) | High (RSA/crypto) |
| **Dependencies** | None | pycryptodome |
| **Best for** | Spam/spam filtering | Wallet recovery (exact matches) |

**Recommendation**: Use Bloom Filter for **spam/scam quick filtering**, use BBF RSA Accumulator (**BTC-fas-scan**) when no false positives are desirable.

---

## Security Considerations

**WARNING**: Bloom filters are **probabilistic**. You will get false positives (address reported as present when it's not), but **never false negatives** (real matches never missed).

| Aspect | Status |
| --- | --- |
| **False positive rate** | Configurable (default 1%) |
| **False negative rate** | 0% (guaranteed) |
| **Collision attacks** | Mitigated by SHA256 hashing |
| **Privacy** | Filter can be rebuilt from your address set only |

For production use where **zero false positives are unacceptable**, prefer the **BBF RSA Accumulator** approach instead.

---

## Troubleshooting

### Memory issues during build

**Reduce expected items or increase RAM **
`python 1_build_bloom_filter.py -i addresses.txt -o filter.bf -n 10000000 -r 0.01`

### Slow verification

**Increase worker count **
`python 2_verify_bloom_filter.py -f filter.bf -w 32`

### High false positive rate

**Increase filter size (reduce FP rate)** 
`python 1_build_bloom_filter.py -i addresses.txt -o filter.bf -r 0.001`

---

## License
Apache 2.0 See License file.

---

## References

| #   | Resource |
| --- | --- |
| **[1]** | Bloom, B. H. (1970): https://doi.org/10.1145/362686.362689 |
| **[2]** | Python `hashlib`: [docs.python.org/3/library/hashlib.html](https://docs.python.org/3/library/hashlib.html) |
| **[3]** | BitCoin Address Formats: [en.bitcoin.it/wiki/Address](https://en.bitcoin.it/wiki/Address) |
| **[4]** | BBF RSA Accumulator: [eprint.iacr.org/2018/1188](https://eprint.iacr.org/2018/1188) |

---
