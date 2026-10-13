#!/usr/bin/env python3
"""Bloom Filter Builder for Bitcoin Addresses - Pure Python (Zero Dependencies)."""

import sys, os, argparse, time, pickle, math, hashlib

def parse_addresses(input_src):
    """Parse addresses from file or STDIN."""
    def line_ok(line):
        addr = line.strip().split()[0].strip()
        return addr if len(addr) >= 20 and len(addr) <= 62 else None
    
    if input_src:
        with open(input_src, 'r', errors='ignore') as f:
            for line in f:
                addr = line_ok(line)
                if addr: yield addr
    else:
        for line in sys.stdin:
            addr = line_ok(line)
            if addr: yield addr

class SimpleBloomFilter:
    """Pure-Python Bloom filter (no external deps beyond stdlib)."""
    
    def __init__(self, expected_items=50000000, fp_rate=0.01, num_hashes=7):
        self.expected_items = expected_items
        self.fp_rate = fp_rate
        self.num_hashes = num_hashes
        
        # Calculate optimal bit size: m = -(n * ln(p)) / (ln(2)^2)
        self.size_in_bits = int(-(expected_items * math.log(fp_rate)) / (math.log(2) ** 2))
        self.num_bytes = (self.size_in_bits + 7) // 8
        self.bit_array = bytearray(self.num_bytes)
    
    def _hashes(self, item: bytes) -> list:
        """Generate multiple hash positions using double hashing."""
        h = hashlib.sha256(item).digest()
        h1 = int.from_bytes(h[:8], 'big')
        h2 = int.from_bytes(h[8:16], 'big')
        
        positions = []
        for i in range(self.num_hashes):
            pos = (h1 + i * h2) % self.size_in_bits
            positions.append(pos)
        return positions
    
    def add(self, item: bytes):
        """Add an item to the filter."""
        for pos in self._hashes(item):
            byte_idx, bit_idx = divmod(pos, 8)
            self.bit_array[byte_idx] |= (1 << bit_idx)
    
    def check(self, item: bytes) -> bool:
        """Check if item is possibly in the filter."""
        for pos in self._hashes(item):
            byte_idx, bit_idx = divmod(pos, 8)
            if not (self.bit_array[byte_idx] & (1 << bit_idx)):
                return False
        return True
    
    def save(self, path: str):
        """Save filter to file with metadata."""
        with open(path, 'wb') as f:
            pickle.dump({
                'size_in_bits': self.size_in_bits,
                'num_bytes': self.num_bytes,
                'num_hashes': self.num_hashes,
                'bit_array': bytes(self.bit_array),
            }, f)
    
    @classmethod
    def load(cls, path: str) -> 'SimpleBloomFilter':
        """Load filter from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        bf = cls.__new__(cls)
        bf.size_in_bits = data['size_in_bits']
        bf.num_bytes = data['num_bytes']
        bf.num_hashes = data['num_hashes']
        bf.bit_array = bytearray(data['bit_array'])
        return bf
    
    @property
    def approx_items(self):
        """Estimated number of items added (rough estimate)."""
        set_bits = sum(bin(b).count('1') for b in self.bit_array)
        if set_bits == 0:
            return 0
        n = -self.size_in_bits * math.log(1 - set_bits/self.size_in_bits) / self.num_hashes
        return int(n)

def build_bloom_filter(input_src, output_path, expected_items=50000000, fp_rate=0.01, num_hashes=7):
    """Build Bloom filter and save to file."""
    print(f"{'='*70}\nBloom Filter Builder\n{'='*70}", flush=True)
    print(f"Expected items:   {expected_items:,}", flush=True)
    print(f"False positive:   {fp_rate:.2%}", flush=True)
    print(f"Hash functions:   {num_hashes}", flush=True)
    print(f"Input:            {input_src or 'STDIN'}", flush=True)
    print()
    
    # Initialize filter
    t0 = time.perf_counter()
    bf = SimpleBloomFilter(expected_items, fp_rate, num_hashes)
    print(f"✓ Filter initialized ({bf.num_bytes / 1024 / 1024:.1f} MB)", flush=True)
    print()
    
    # Add addresses
    print("[Adding addresses...]")
    count = 0
    for addr in parse_addresses(input_src):
        bf.add(addr.encode())
        count += 1
        if count % 1000000 == 0:
            print(f"    Added {count:,} addresses...", flush=True)
    
    elapsed = time.perf_counter() - t0
    print(f"\n✓ Added {count:,} addresses in {elapsed:.1f}s ({count/elapsed:,.0f}/sec)", flush=True)
    
    # Save
    print(f"\n[Saving to {output_path}...]")
    bf.save(output_path)
    
    # Stats
    print(f"\n{'='*70}\nCOMPLETE\n{'='*70}", flush=True)
    print(f"Items added:      {count:>12,}")
    print(f"Filter size:      {os.path.getsize(output_path):>12,} bytes ({os.path.getsize(output_path)/1024/1024:.1f} MB)")
    print(f"Bit size:         {bf.size_in_bits:>12,} bits ({bf.size_in_bits/1024/1024:.1f} MB)")
    print(f"Hash functions:   {num_hashes:>12}")
    print(f"Build time:       {elapsed:>12.2f}s")
    print(f"Throughput:       {count/elapsed:>12,.0f} items/sec")
    print(f"{'='*70}\n", flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bloom Filter Builder')
    parser.add_argument('-i', '--input', dest='src', default=None)
    parser.add_argument('-o', '--output', default='address_filter.bf')
    parser.add_argument('-n', '--expected-items', type=int, default=50000000)
    parser.add_argument('-r', '--fp-rate', type=float, default=0.01)
    parser.add_argument('-k', '--num-hashes', type=int, default=7)
    args = parser.parse_args()
    
    build_bloom_filter(args.src, args.output, args.expected_items, args.fp_rate, args.num_hashes)