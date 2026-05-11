"""
BB84 Protocol Metrics and Analysis
"""

import numpy as np


class BB84Metrics:
    """
    Calculate and track BB84 protocol performance metrics.
    """
    
    def __init__(self):
        """Initialize metrics tracker."""
        self.results = {}
    
    def calculate_qber(self, alice_key, bob_key, sample_size=None):
        """
        Calculate Quantum Bit Error Rate.
        
        Args:
            alice_key (np.ndarray): Alice's sifted key
            bob_key (np.ndarray): Bob's sifted key
            sample_size (int): Number of bits to sample for error checking
                              If None, uses 50% of key
        
        Returns:
            tuple: (qber, sampled_bits, error_count)
        """
        if len(alice_key) == 0:
            return 0.0, 0, 0
        
        # Default: sample 50% of the key
        if sample_size is None:
            sample_size = max(1, len(alice_key) // 2)
        
        # Ensure we don't sample more than available
        sample_size = min(sample_size, len(alice_key))
        
        # Randomly sample indices
        sample_indices = np.random.choice(len(alice_key), sample_size, replace=False)
        
        # Count errors in sampled bits
        alice_sample = alice_key[sample_indices]
        bob_sample = bob_key[sample_indices]
        errors = np.sum(alice_sample != bob_sample)
        
        # Calculate QBER
        qber = (errors / sample_size) * 100 if sample_size > 0 else 0.0
        
        return qber, sample_size, errors
    
    def calculate_final_key_length(self, sifted_key_length, sampled_bits):
        """
        Calculate final key length after privacy amplification.
        
        Args:
            sifted_key_length (int): Length of sifted key
            sampled_bits (int): Number of bits used for error detection
            
        Returns:
            int: Final usable key length
        """
        return max(0, sifted_key_length - sampled_bits)
    
    def calculate_key_generation_rate(self, final_key_length, initial_qubits):
        """
        Calculate key generation rate.
        
        Args:
            final_key_length (int): Final usable key bits
            initial_qubits (int): Initial qubits transmitted
            
        Returns:
            float: Key generation rate (0-1)
        """
        if initial_qubits == 0:
            return 0.0
        return final_key_length / initial_qubits
    
    def calculate_all_metrics(self, initial_qubits, lost_qubits, 
                            alice_key, bob_key, sample_size=None):
        """
        Calculate all BB84 metrics.
        
        Args:
            initial_qubits (int): Number of qubits initially transmitted
            lost_qubits (int): Number of qubits lost in channel
            alice_key (np.ndarray): Alice's sifted key
            bob_key (np.ndarray): Bob's sifted key
            sample_size (int): Bits to sample for error detection
            
        Returns:
            dict: All calculated metrics
        """
        # Calculate QBER
        qber, sampled_bits, errors = self.calculate_qber(alice_key, bob_key, sample_size)
        
        # Calculate final key length
        sifted_length = len(alice_key)
        final_key_length = self.calculate_final_key_length(sifted_length, sampled_bits)
        
        # Calculate key generation rate
        key_rate = self.calculate_key_generation_rate(final_key_length, initial_qubits)
        
        # Store results
        self.results = {
            'initial_qubits': initial_qubits,
            'lost_qubits': lost_qubits,
            'received_qubits': initial_qubits - lost_qubits,
            'sifted_key_length': sifted_length,
            'sampled_bits': sampled_bits,
            'error_count': errors,
            'qber': qber,
            'final_key_length': final_key_length,
            'key_generation_rate': key_rate
        }
        
        return self.results
    
    def print_metrics(self):
        """Print all metrics in a formatted way."""
        if not self.results:
            print("No metrics calculated yet.")
            return
        
        print("\n" + "="*50)
        print("BB84 PROTOCOL METRICS")
        print("="*50)
        print(f"Initial Qubits Transmitted:  {self.results['initial_qubits']}")
        print(f"Qubits Lost in Channel:      {self.results['lost_qubits']}")
        print(f"Qubits Received by Bob:      {self.results['received_qubits']}")
        print(f"Sifted Key Length:           {self.results['sifted_key_length']}")
        print(f"Bits Used for Error Check:   {self.results['sampled_bits']}")
        print(f"Errors Detected:             {self.results['error_count']}")
        print(f"QBER:                        {self.results['qber']:.2f}%")
        print(f"Final Key Length:            {self.results['final_key_length']}")
        print(f"Key Generation Rate:         {self.results['key_generation_rate']:.4f}")
        print("="*50 + "\n")


# Test
if __name__ == "__main__":
    from bb84_protocol import BB84Protocol
    from noise_models import NoiseModel
    
    print("Testing Metrics Calculation...")
    
    # Run protocol with noise
    bb84 = BB84Protocol(n_qubits=1000)
    qubits = bb84.alice_prepare_qubits()
    
    # Apply noise to channel
    noise = NoiseModel(depolarization_prob=0.05, photon_loss_prob=0.1)
    noisy_qubits, lost_indices = noise.apply_noise_to_channel(qubits)
    
    # Remove lost qubits from Alice's data before Bob measures
    alice_bits_after_loss = np.delete(bb84.alice_bits, lost_indices)
    alice_bases_after_loss = np.delete(bb84.alice_bases, lost_indices)
    
    # Bob measures actual arrived qubits
    bob_results = bb84.bob_measure_qubits(noisy_qubits)
    
    # Update bb84 object with corrected data
    bb84.alice_bits = alice_bits_after_loss
    bb84.alice_bases = alice_bases_after_loss
    
    # Perform sifting
    bb84.sift_keys()
    
    # Calculate metrics
    metrics = BB84Metrics()
    results = metrics.calculate_all_metrics(
        initial_qubits=1000,
        lost_qubits=len(lost_indices),
        alice_key=bb84.sifted_key_alice,
        bob_key=bb84.sifted_key_bob
    )
    
    metrics.print_metrics()