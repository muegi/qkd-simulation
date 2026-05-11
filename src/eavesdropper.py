"""
Eavesdropper (Eve) - Intercept-Resend Attack
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class Eavesdropper:
    """
    Implements Eve's intercept-resend attack on the quantum channel
    """
    
    def __init__(self, enabled=False):
        """
        Initialize eavesdropper
        
        Args:
            enabled (bool): Whether Eve is active
        """
        self.enabled = enabled
        self.intercepted_count = 0
        self.eve_bases = None
        self.eve_results = None
    
    def intercept_and_resend(self, qubits):
        """
        Eve intercepts qubits, measures them, and resends new qubits
        
        Args:
            qubits (list): List of quantum circuits from Alice
            
        Returns:
            list: New qubits prepared by Eve based on her measurements
        """
        if not self.enabled:
            return qubits
        
        # Generate random measurement bases for Eve
        self.eve_bases = np.random.randint(0, 2, len(qubits))
        self.eve_results = []
        
        resent_qubits = []
        simulator = AerSimulator()
        
        for qc, eve_basis in zip(qubits, self.eve_bases):
            # Eve measures the qubit
            measured_qc = qc.copy()
            
            # Apply measurement in Eve's chosen basis
            if eve_basis == 1:  # Diagonal basis
                measured_qc.h(0)
            
            # Measure qubit 0 to classical bit 0
            measured_qc.measure(0, 0)
            
            # Simulate measurement
            job = simulator.run(measured_qc, shots=1)
            result = job.result()
            counts = result.get_counts()
            
            # Extract measurement outcome (0 or 1)
            eve_outcome = int(list(counts.keys())[0])
            
            self.eve_results.append(eve_outcome)
            self.intercepted_count += 1
            
            # Eve prepares a new qubit based on her measurement
            new_qc = QuantumCircuit(1, 1)
            if eve_outcome == 1:
                new_qc.x(0)
            if eve_basis == 1:
                new_qc.h(0)
            
            resent_qubits.append(new_qc)
        
        return resent_qubits
    
    def reset(self):
        """Reset eavesdropper statistics"""
        self.intercepted_count = 0
        self.eve_bases = None
        self.eve_results = None


# Test
if __name__ == "__main__":
    from bb84_protocol import BB84Protocol
    
    print("Testing Eavesdropper...")
    
    # Test without Eve
    print("\n--- Without Eve ---")
    bb84 = BB84Protocol(n_qubits=1000)
    qubits = bb84.alice_prepare_qubits()
    bb84.bob_measure_qubits(qubits)
    bb84.sift_keys()
    
    errors = np.sum(bb84.sifted_key_alice != bb84.sifted_key_bob)
    qber = errors / len(bb84.sifted_key_alice) * 100
    print(f"QBER without Eve: {qber:.2f}%")
    
    # Test with Eve
    print("\n--- With Eve ---")
    bb84 = BB84Protocol(n_qubits=1000)
    qubits = bb84.alice_prepare_qubits()
    
    eve = Eavesdropper(enabled=True)
    intercepted_qubits = eve.intercept_and_resend(qubits)
    
    bb84.bob_measure_qubits(intercepted_qubits)
    bb84.sift_keys()
    
    errors = np.sum(bb84.sifted_key_alice != bb84.sifted_key_bob)
    qber = errors / len(bb84.sifted_key_alice) * 100
    print(f"QBER with Eve: {qber:.2f}%")
    print(f"Intercepted qubits: {eve.intercepted_count}")