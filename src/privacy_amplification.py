"""
Privacy Amplification
"""

import numpy as np
from typing import Tuple


class PrivacyAmplification:
    """
    Implements privacy amplification using universal hashing (Toeplitz matrices)
    
    Based on the leftover hash lemma, this compresses the reconciled key to
    remove Eve's partial information, producing a shorter but provably secure key
    """
    
    def __init__(self):
        """Initialize privacy amplification"""
        self.compression_ratio = 0.0
        self.bits_removed = 0
    
    def binary_entropy(self, p: float) -> float:
        """
        Calculate binary entropy H(p)
        
        Args:
            p: Probability (0 to 1)
            
        Returns:
            Binary entropy value
        """
        if p <= 0 or p >= 1:
            return 0.0
        
        return -p * np.log2(p) - (1 - p) * np.log2(1 - p)
    
    def calculate_secure_length(self, key_length: int, qber: float, 
                               security_parameter: float = 1e-10) -> int:
        """
        Calculate final secure key length using privacy amplification bound
        
        Based on: n_final ≈ n × [1 - H(QBER)] - log₂(1/ε)
        
        Args:
            key_length: Length of error-corrected key
            qber: Quantum bit error rate (as percentage)
            security_parameter: Security parameter ε (typically 10⁻⁹ to 10⁻¹⁰)
            
        Returns:
            Final secure key length after privacy amplification
        """
        # Convert QBER to error rate
        error_rate = qber / 100.0
        
        # Calculate binary entropy
        h_qber = self.binary_entropy(error_rate)
        
        # Security parameter term: log₂(1/ε)
        security_bits = int(np.ceil(-np.log2(security_parameter)))
        
        # Apply privacy amplification bound
        # n_final = n × (1 - H(QBER)) - security_bits
        secure_length = int(key_length * (1 - h_qber)) - security_bits
        
        # Ensure non-negative
        secure_length = max(0, secure_length)
        
        self.compression_ratio = secure_length / key_length if key_length > 0 else 0
        self.bits_removed = key_length - secure_length
        
        return secure_length
    
    def generate_toeplitz_matrix(self, n: int, m: int, seed: int = None) -> np.ndarray:
        """
        Generate a random Toeplitz matrix for universal hashing
        
        A Toeplitz matrix has constant diagonals, each descending diagonal
        from left to right is constant
        
        Note: In real QKD, Alice generates this matrix and publicly shares the
        parameters (first_row, first_col) with Bob so both can compute the same
        hash. The seed parameter simulates this public sharing: if Alice and Bob
        both use the same seed, they generate identical matrices. This simulation
        uses a fixed seed to represent this coordinated matrix use,
        though only Bob's hash is actually computed.
        
        Args:
            n: Input length (original key length)
            m: Output length (compressed key length)
            seed: Optional random seed for reproducible matrix generation
            
        Returns:
            m×n Toeplitz matrix
        """
        # Set seed if provided (for reproducibility)
        if seed is not None:
            np.random.seed(seed)
        
        # Generate random bits for first row and first column
        first_row = np.random.randint(0, 2, n)
        first_col = np.random.randint(0, 2, m)
        first_col[0] = first_row[0]  # Overlap at [0,0]
        
        # Build Toeplitz matrix
        matrix = np.zeros((m, n), dtype=int)
        
        for i in range(m):
            for j in range(n):
                if i <= j:
                    matrix[i, j] = first_row[j - i]
                else:
                    matrix[i, j] = first_col[i - j]
        
        return matrix
    
    def apply_universal_hash(self, key: np.ndarray, final_length: int, seed: int = None) -> np.ndarray:
        """
        Apply universal hashing using Toeplitz matrix multiplication
        
        Args:
            key: Input key (error-corrected)
            final_length: output length
            seed: Set as 42 for reproducible hashing
            
        Returns:
            Compressed secure key
        """
        n = len(key)
        
        if final_length >= n:
            # No compression needed
            return key
        
        if final_length <= 0:
            return np.array([])
        
        # Generate Toeplitz matrix (with optional seed for reproducibility)
        toeplitz = self.generate_toeplitz_matrix(n, final_length, seed)
        
        # Matrix multiplication in GF(2): (T × key) mod 2
        # XOR of selected positions
        final_key = np.dot(toeplitz, key) % 2
        
        return final_key
    
    def amplify(self, key: np.ndarray, qber: float, 
                security_parameter: float = 1e-10, seed: int = None) -> Tuple[np.ndarray, dict]:
        """
        Perform complete privacy amplification
        
        Args:
            key: Error-corrected key
            qber: Measured QBER (percentage)
            security_parameter: Security parameter ε
            seed: Optional seed for reproducible hashing (default None = random each time)
            
        Returns:
            Tuple of (final_secure_key, statistics_dict)
        """
        # Calculate secure length
        final_length = self.calculate_secure_length(
            len(key), qber, security_parameter
        )
        
        if final_length <= 0:
            return np.array([]), {
                'original_length': len(key),
                'final_length': 0,
                'compression_ratio': 0.0,
                'bits_removed': len(key),
                'binary_entropy': self.binary_entropy(qber / 100),
                'security_parameter': security_parameter
            }
        
        # Apply universal hashing (with optional seed)
        final_key = self.apply_universal_hash(key, final_length, seed)
        
        stats = {
            'original_length': len(key),
            'final_length': final_length,
            'compression_ratio': self.compression_ratio,
            'bits_removed': self.bits_removed,
            'binary_entropy': self.binary_entropy(qber / 100),
            'security_parameter': security_parameter
        }
        
        return final_key, stats
    
    def reset(self):
        """Reset statistics."""
        self.compression_ratio = 0.0
        self.bits_removed = 0


# Test
if __name__ == "__main__":
    print("="*60)
    print("Testing Privacy Amplification...")
    print("="*60)
    
    # Test 1: Basic functionality
    print("\nTest 1: Basic PA with 10% QBER")
    print("-"*60)
    
    key = np.random.randint(0, 2, 1000)
    pa = PrivacyAmplification()
    final_key, stats = pa.amplify(key, qber=10.0, security_parameter=1e-10)
    
    print(f"Original key length: {len(key)}")
    print(f"Final secure key length: {stats['final_length']}")
    print(f"Compression ratio: {stats['compression_ratio']:.3f}")
    print(f"Binary entropy H(0.10): {stats['binary_entropy']:.4f}")
    print(f"Bits removed: {stats['bits_removed']}")
    print(f"Security parameter: {stats['security_parameter']}")
    print(f"\nFinal key (first 50 bits): {final_key[:50]}")
    
    # Test 2: Reproducibility with seed
    print("\n" + "="*60)
    print("Test 2: Reproducibility with Fixed Seed")
    print("-"*60)
    
    test_key = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 0])
    
    pa1 = PrivacyAmplification()
    result1, _ = pa1.amplify(test_key, qber=10.0, seed=42)
    
    pa2 = PrivacyAmplification()
    result2, _ = pa2.amplify(test_key, qber=10.0, seed=42)
    
    print(f"Input key: {test_key}")
    print(f"Result 1 (seed=42): {result1}")
    print(f"Result 2 (seed=42): {result2}")
    print(f"Results match: {np.array_equal(result1, result2)}")
    
    # Test 3: Different seeds produce different outputs
    print("\n" + "="*60)
    print("Test 3: Different Seeds → Different Outputs")
    print("-"*60)
    
    pa3 = PrivacyAmplification()
    result3, _ = pa3.amplify(test_key, qber=10.0, seed=99)
    
    print(f"Input key: {test_key}")
    print(f"Result (seed=42): {result1}")
    print(f"Result (seed=99): {result3}")
    print(f"Results differ: {not np.array_equal(result1, result3)}")
    
    # Test 4: Multiple QBER values
    print("\n" + "="*60)
    print("Test 4: PA Across Different QBER Values")
    print("-"*60)
    
    test_qbers = [5.0, 10.0, 15.0, 20.0]
    print(f"\n{'QBER':<8} {'Entropy':<10} {'Input':<8} {'Output':<8} {'Ratio':<8}")
    print("-"*60)
    
    for qber in test_qbers:
        pa_test = PrivacyAmplification()
        test_input = np.random.randint(0, 2, 1000)
        final, stats = pa_test.amplify(test_input, qber=qber, seed=42)
        
        print(f"{qber:>6.1f}%  {stats['binary_entropy']:<10.4f} {len(test_input):<8} {stats['final_length']:<8} {stats['compression_ratio']:<8.3f}")
    
    # Test 5: Edge cases
    print("\n" + "="*60)
    print("Test 5: Edge Cases")
    print("-"*60)
    
    # Very high QBER (should produce zero or tiny key)
    pa_edge1 = PrivacyAmplification()
    edge_key1 = np.random.randint(0, 2, 100)
    final_edge1, stats_edge1 = pa_edge1.amplify(edge_key1, qber=40.0)
    print(f"\nHigh QBER (40%): {len(edge_key1)} → {stats_edge1['final_length']} bits")
    
    # Zero QBER (should keep most bits)
    pa_edge2 = PrivacyAmplification()
    edge_key2 = np.random.randint(0, 2, 100)
    final_edge2, stats_edge2 = pa_edge2.amplify(edge_key2, qber=0.5)
    print(f"Low QBER (0.5%): {len(edge_key2)} → {stats_edge2['final_length']} bits")
    
    print("\n" + "="*60)
    print("All tests completed")
    print("="*60)