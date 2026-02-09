"""
BB84 Quantum Key Distribution Protocol Implementation
"""

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator


class BB84Protocol:
    """
    Implements the BB84 quantum key distribution protocol.
    
    Attributes:
        n_qubits (int): Number of qubits to transmit
        alice_bits (np.ndarray): Alice's random classical bits
        alice_bases (np.ndarray): Alice's random encoding bases
        bob_bases (np.ndarray): Bob's random measurement bases
        bob_results (np.ndarray): Bob's measurement outcomes
    """
    
    def __init__(self, n_qubits=100):
        """
        Initialize BB84 protocol.
        
        Args:
            n_qubits (int): Number of qubits to transmit (default: 100)
        """
        self.n_qubits = n_qubits
        self.alice_bits = None
        self.alice_bases = None
        self.bob_bases = None
        self.bob_results = None
        self.sifted_key_alice = None
        self.sifted_key_bob = None
        
    def generate_random_bits(self, n):
        """
        Generate random classical bits.
        
        Args:
            n (int): Number of bits to generate
            
        Returns:
            np.ndarray: Array of random bits (0 or 1)
        """
        return np.random.randint(0, 2, n)
    
    def encode_qubit(self, bit, basis):
        """
        Encode a classical bit into a quantum state.
        
        Args:
            bit (int): Classical bit (0 or 1)
            basis (int): Encoding basis (0 = rectilinear, 1 = diagonal)
            
        Returns:
            QuantumCircuit: Quantum circuit with encoded qubit
        """
        qc = QuantumCircuit(1, 1)
        
        # Encode bit
        if bit == 1:
            qc.x(0)  # Apply X gate to flip |0⟩ to |1⟩
        
        # Apply basis rotation
        if basis == 1:  # Diagonal basis
            qc.h(0)  # Apply Hadamard to create superposition
            
        return qc
    
    def measure_qubit(self, qc, basis):
        """
        Measure a qubit in the specified basis.
        
        Args:
            qc (QuantumCircuit): Quantum circuit containing the qubit
            basis (int): Measurement basis (0 = rectilinear, 1 = diagonal)
            
        Returns:
            QuantumCircuit: Circuit with measurement added
        """
        # If measuring in diagonal basis, rotate back to rectilinear first
        if basis == 1:
            qc.h(0)
        
        qc.measure(0, 0)
        return qc
    
    def alice_prepare_qubits(self):
        """
        Alice generates random bits and bases, then prepares qubits.
        
        Returns:
            list: List of quantum circuits (prepared qubits)
        """
        # Generate random bits and bases
        self.alice_bits = self.generate_random_bits(self.n_qubits)
        self.alice_bases = self.generate_random_bits(self.n_qubits)
        
        # Prepare qubits
        qubits = []
        for bit, basis in zip(self.alice_bits, self.alice_bases):
            qc = self.encode_qubit(bit, basis)
            qubits.append(qc)
        
        return qubits
    
    def bob_measure_qubits(self, qubits):
        """
        Bob randomly selects measurement bases and measures qubits.
        
        Args:
            qubits (list): List of quantum circuits to measure
            
        Returns:
            np.ndarray: Bob's measurement results
        """
        # Generate random measurement bases
        self.bob_bases = self.generate_random_bits(len(qubits))
        
        # Measure each qubit
        results = []
        simulator = AerSimulator()
        
        for qc, basis in zip(qubits, self.bob_bases):
            # Create a copy to avoid modifying original
            measured_qc = qc.copy()
            measured_qc = self.measure_qubit(measured_qc, basis)
            
            # Simulate measurement
            job = simulator.run(measured_qc, shots=1)
            result = job.result()
            counts = result.get_counts()
            
            # Extract measurement outcome (0 or 1)
            outcome = int(list(counts.keys())[0])
            results.append(outcome)
        
        self.bob_results = np.array(results)
        return self.bob_results
    
    def sift_keys(self):
        """
        Perform basis reconciliation (sifting).
        Keep only bits where Alice and Bob used the same basis.
        
        Returns:
            tuple: (sifted_key_alice, sifted_key_bob)
        """
        # Find matching bases
        matching_bases = self.alice_bases == self.bob_bases
        
        # Keep only matching bits
        self.sifted_key_alice = self.alice_bits[matching_bases]
        self.sifted_key_bob = self.bob_results[matching_bases]
        
        return self.sifted_key_alice, self.sifted_key_bob
    
    def run_protocol(self):
        """
        Execute the complete BB84 protocol.
        
        Returns:
            dict: Results containing keys and metrics
        """
        # Alice prepares qubits
        qubits = self.alice_prepare_qubits()
        
        # Bob measures qubits
        self.bob_measure_qubits(qubits)
        
        # Sift keys (basis reconciliation)
        self.sift_keys()
        
        return {
            'alice_key': self.sifted_key_alice,
            'bob_key': self.sifted_key_bob,
            'sifted_length': len(self.sifted_key_alice),
            'initial_qubits': self.n_qubits
        }


# Test
if __name__ == "__main__":
    print("Testing BB84 Protocol...")
    bb84 = BB84Protocol(n_qubits=100)
    results = bb84.run_protocol()
    
    print(f"Initial qubits: {results['initial_qubits']}")
    print(f"Sifted key length: {results['sifted_length']}")
    print(f"Alice's key (first 10): {results['alice_key'][:10]}")
    print(f"Bob's key (first 10): {results['bob_key'][:10]}")
    print(f"Keys match: {np.array_equal(results['alice_key'], results['bob_key'])}")