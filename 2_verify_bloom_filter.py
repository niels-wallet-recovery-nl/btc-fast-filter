#!/usr/bin/env python3
"""Bloom Filter Verifier - Fast Parallel Membership Check - Pure Python."""

import sys, os, argparse, time, hashlib
from concurrent.futures import ThreadPoolExecutor

class SimpleBloomFilter:
    """Pure-Python Bloom filter (no external deps)."""
    
    def __init__(self, expected_items=50000000, fp_rate=0.01, num_hashes=7):
        import math
        self.size_in_bits = int(-(expected_items * math.log(fp_rate)) / (math.log(2) ** 2))
        self.num_bytes = (self.size_in_bits + 7) // 8
        self.num_hashes = num_hashes
        self.bit_array = bytearray(self.num_bytes)
    
    def _hashes(self, item: bytes) -> list:
        h = hashlib.sha256(item).digest()
        h1 = int.from_bytes(h[:8], 'big')
        h2 = int.from_bytes(h[8:16], 'big')
        positions = []
        for i in range(self.num_hashes):
            pos = (h1 + i * h2) % self.size_in_bits
            positions.append(pos)
        return positions
    
    def check(self, item: bytes) -> bool:
        for pos in self._hashes(item):
            byte_idx, bit_idx = divmod(pos, 8)
            if not (self.bit_array[byte_idx] & (1 << bit_idx)):
                return False
        return True
    
    @classmethod
    def load(cls, path: str) -> 'SimpleBloomFilter':
        import pickle
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        bf = cls.__new__(cls)
        bf.size_in_bits = data['size_in_bits']
        bf.num_bytes = data['num_bytes']
        bf.num_hashes = data['num_hashes']
        bf.bit_array = bytearray(data['bit_array'])
        return bf

def parse_addresses():
    """Parse addresses from STDIN."""
    for line in sys.stdin:
        addr = line.strip().split()[0].strip()
        if len(addr) >= 20:
            yield addr

def check_address(args):
    """Check one address - returns (address, found)."""
    addr, bf = args
    return addr, bf.check(addr.encode())

def verify_parallel(filter_path, workers=16):
    """Verify addresses from STDIN in parallel."""
    print(f"[DEBUG] Loading Bloom filter from {filter_path}...", file=sys.stderr, flush=True)
    t0_load = time.perf_counter()
    bf = SimpleBloomFilter.load(filter_path)
    t0_total = time.perf_counter()
    
    elapsed = time.perf_counter() - t0_load
    print(f"[DEBUG] Loaded {bf.num_bytes/1024/1024:.1f} MB filter in {elapsed*1000:.1f}ms", 
          file=sys.stderr, flush=True)
    
    # Collect all addresses first
    addresses = list(parse_addresses())
    print(f"[DEBUG] {len(addresses):,} addresses to check", file=sys.stderr, flush=True)
    
    if not addresses:
        return
    
    # Create tasks
    tasks = [(addr, bf) for addr in addresses]
    
    # Verify in parallel - SIMPLE approach using pool.map()
    matches = 0
    start = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(check_address, tasks)
        
        for addr, found in results:
            if found:
                matches += 1
                print(addr, flush=True)
    
    elapsed = time.perf_counter() - start
    avg_us = (elapsed / len(addresses)) * 1_000_000 if addresses else 0
    
    print(f"[DEBUG] Scanned {len(addresses):,} | {matches:,} matches | {avg_us:.1f}µs/addr avg | {elapsed:.1f}s total", 
          file=sys.stderr, flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bloom Filter Address Verifier')
    parser.add_argument('-f', '--file', required=True, help='Bloom filter file')
    parser.add_argument('-w', '--workers', type=int, default=16)
    args = parser.parse_args()
    
    verify_parallel(args.file, args.workers)