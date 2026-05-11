"""
CASCADE Error Correction Algorithm
"""

import numpy as np
from typing import Tuple, Dict


class CASCADEErrorCorrection:
    """
    Implements CASCADE error correction algorithm
    
    """
    
    def __init__(self):
        self.bits_disclosed = 0
        self.errors_corrected = 0
        self.passes_run = 0
    
    def parity(self, bits: np.ndarray) -> int:
        """Calculate even (0) or odd (1) parity"""
        return int(np.sum(bits) % 2)
    
    def binary_search(self, alice_block: np.ndarray, bob_block: np.ndarray, 
                     block_start_idx: int) -> int:
        """
        Binary search to find error position in a block
        
        Returns:
            Global index of error, or -1 if no error
        """
        if len(alice_block) == 0:
            return -1
        
        # Compare parities
        alice_par = self.parity(alice_block)
        bob_par = self.parity(bob_block)
        self.bits_disclosed += 1
        
        if alice_par == bob_par:
            return -1  # No error in this block
        
        # Base case: single bit
        if len(alice_block) == 1:
            return block_start_idx
        
        # Recursive case: split in half
        mid = len(alice_block) // 2
        
        # Search left half
        left_error = self.binary_search(
            alice_block[:mid], 
            bob_block[:mid], 
            block_start_idx
        )
        
        if left_error != -1:
            return left_error
        
        # Search right half
        right_error = self.binary_search(
            alice_block[mid:], 
            bob_block[mid:], 
            block_start_idx + mid
        )
        
        return right_error
    
    def cascade_pass(self, alice_key: np.ndarray, bob_key: np.ndarray,
                    block_size: int, shuffle_seed: int = None) -> Tuple[np.ndarray, int]:
        """
        Single CASCADE pass
        
        Returns:
            (corrected_bob_key, num_errors_found)
        """
        n = len(alice_key)
        bob_corrected = bob_key.copy()
        errors_found = 0
        
        # Shuffle if seed provided (passes 2+)
        if shuffle_seed is not None:
            np.random.seed(shuffle_seed)
            perm = np.random.permutation(n)
            inverse_perm = np.argsort(perm)
            
            alice_shuffled = alice_key[perm]
            bob_shuffled = bob_corrected[perm]
        else:
            perm = np.arange(n)
            inverse_perm = np.arange(n)
            alice_shuffled = alice_key
            bob_shuffled = bob_corrected
        
        # Process blocks
        num_blocks = int(np.ceil(n / block_size))
        
        for block_idx in range(num_blocks):
            start = block_idx * block_size
            end = min(start + block_size, n)
            
            alice_block = alice_shuffled[start:end]
            bob_block = bob_shuffled[start:end]
            
            # Find error in this block
            error_idx = self.binary_search(alice_block, bob_block, start)
            
            if error_idx != -1:
                # Correct the error
                bob_shuffled[error_idx] = 1 - bob_shuffled[error_idx]
                errors_found += 1
                self.errors_corrected += 1
        
        # Unshuffle
        bob_corrected = bob_shuffled[inverse_perm]
        
        return bob_corrected, errors_found
    
    def run_cascade(self, alice_key: np.ndarray, bob_key: np.ndarray,
                   estimated_qber: float, num_passes: int = 4) -> Tuple[np.ndarray, Dict]:
        """
        Run complete CASCADE with multiple passes
        """
        self.bits_disclosed = 0
        self.errors_corrected = 0
        self.passes_run = 0
        
        n = len(alice_key)
        bob_corrected = bob_key.copy()
        
        # Initial block size based on QBER
        if estimated_qber > 0:
            k0 = max(2, int(0.73 / (estimated_qber / 100)))
        else:
            k0 = max(2, n // 4)
        
        # Multiple passes with increasing block sizes
        for pass_num in range(num_passes):
            # Calculate block size for this pass
            if pass_num == 0:
                block_size = k0
                shuffle_seed = None  # No shuffle first pass
            else:
                block_size = k0 * (2 ** (pass_num - 1))
                shuffle_seed = pass_num * 1000  # Different seed each pass
            
            block_size = min(block_size, n)  # Don't exceed key length
            
            # Perform pass
            bob_corrected, errors_found = self.cascade_pass(
                alice_key, bob_corrected, block_size, shuffle_seed
            )
            
            self.passes_run += 1
            
            # Stop if no errors found
            if errors_found == 0:
                break
        
        # Final check
        remaining_errors = np.sum(alice_key != bob_corrected)
        
        return bob_corrected, {
            'errors_corrected': self.errors_corrected,
            'bits_disclosed': self.bits_disclosed,
            'passes_completed': self.passes_run,
            'remaining_errors': int(remaining_errors),
            'correction_success': (remaining_errors == 0)
        }
    
    def reset(self):
        self.bits_disclosed = 0
        self.errors_corrected = 0
        self.passes_run = 0


# Test CASCADE cases
if __name__ == "__main__":
    print("="*60)
    print("Testing CASCADE Error Correction...")
    print("="*60)
    
    # Test 1: Small key with few errors
    print("\nTest 1: Small key (16 bits, 3 errors)")
    alice1 = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1])
    bob1 = alice1.copy()
    
    # Introduce errors at positions 2, 7, 12 (0-indexed)
    # In human counting (1-indexed): positions 3, 8, 13 
    bob1[2] = 1 - bob1[2]   # Flip
    bob1[7] = 1 - bob1[7]   # Flip
    bob1[12] = 1 - bob1[12] # Flip
    
    print(f"Alice:  {alice1}")
    print(f"Bob:    {bob1}")
    print(f"Errors at 0-indexed positions: [2, 7, 12]"   )
    print(f"Or in human counting (1-indexed): [3, 8, 13]")
    
    cascade1 = CASCADEErrorCorrection()
    corrected1, stats1 = cascade1.run_cascade(alice1, bob1, estimated_qber=18.75, num_passes=6)
    
    print(f"\nCorrected: {corrected1}")
    print(f"Match: {np.array_equal(alice1, corrected1)}")
    print(f"Stats: {stats1}")
    
    # Test 2: Larger key
    print("\n" + "="*60)
    print("Test 2: Larger key (100 bits, 10% error rate)")
    
    alice2 = np.random.randint(0, 2, 100)
    bob2 = alice2.copy()
    
    # Introduce 10 random errors
    error_positions = np.random.choice(100, 10, replace=False)
    for pos in error_positions:
        bob2[pos] = 1 - bob2[pos]
    
    print(f"Key length: 100 bits")
    print(f"Errors introduced: 10")
    print(f"Error positions: {sorted(error_positions)}")
    
    cascade2 = CASCADEErrorCorrection()
    corrected2, stats2 = cascade2.run_cascade(alice2, bob2, estimated_qber=10.0, num_passes=8)
    
    print(f"\nMatch after correction: {np.array_equal(alice2, corrected2)}")
    print(f"Stats: {stats2}")
    
    # Test 3: High error rate
    print("\n" + "="*60)
    print("Test 3: High error rate (50 bits, 20% errors)")
    
    alice3 = np.random.randint(0, 2, 50)
    bob3 = alice3.copy()
    error_positions3 = np.random.choice(50, 10, replace=False)
    for pos in error_positions3:
        bob3[pos] = 1 - bob3[pos]
    
    cascade3 = CASCADEErrorCorrection()
    corrected3, stats3 = cascade3.run_cascade(alice3, bob3, estimated_qber=20.0, num_passes=8)
    
    print(f"Match: {np.array_equal(alice3, corrected3)}")
    print(f"Stats: {stats3}")
    
    print("\n" + "="*60)