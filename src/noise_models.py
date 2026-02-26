"""
Quantum Channel Noise Models
"""

import numpy as np
from qiskit import QuantumCircuit


class NoiseModel:
    """
    Implements quantum channel noise: depolarization and photon loss.
    """
    
    def __init__(self, depolarization_prob=0.0, photon_loss_prob=0.0):
        """
        Initialize noise model.
        
        Args:
            depolarization_prob (float): Probability of depolarization (0-1)
            photon_loss_prob (float): Probability of photon loss (0-1)
        """
        self.depolarization_prob = depolarization_prob
        self.photon_loss_prob = photon_loss_prob
        self.lost_qubits = 0
    
    def apply_photon_loss(self, qubits):
        """
        Simulate photon loss by randomly dropping qubits.
        
        Args:
            qubits (list): List of quantum circuits
            
        Returns:
            tuple: (remaining_qubits, lost_indices)
        """
        remaining_qubits = []
        lost_indices = []
        
        for idx, qc in enumerate(qubits):
            # Randomly determine if photon is lost
            if np.random.random() < self.photon_loss_prob:
                lost_indices.append(idx)
                self.lost_qubits += 1
            else:
                remaining_qubits.append(qc)
        
        return remaining_qubits, lost_indices
    
    def apply_depolarization(self, qc):
        """
        Apply depolarization noise to a qubit.
        Randomly applies X (bit-flip), Z (phase-flip), or Y (both).
        
        Args:
            qc (QuantumCircuit): Quantum circuit
            
        Returns:
            QuantumCircuit: Noisy quantum circuit
        """
        if np.random.random() < self.depolarization_prob:
            # Randomly choose error type
            error_type = np.random.choice(['X', 'Y', 'Z'])
            
            if error_type == 'X':
                qc.x(0)  # Bit flip
            elif error_type == 'Y':
                qc.y(0)  # Bit and phase flip
            elif error_type == 'Z':
                qc.z(0)  # Phase flip
        
        return qc
    
    def apply_noise_to_channel(self, qubits):
        """
        Apply both photon loss and depolarization to a quantum channel.
        
        Args:
            qubits (list): List of quantum circuits
            
        Returns:
            tuple: (noisy_qubits, lost_indices)
        """
        # First apply photon loss
        remaining_qubits, lost_indices = self.apply_photon_loss(qubits)
        
        # Then apply depolarization to remaining qubits
        noisy_qubits = []
        for qc in remaining_qubits:
            noisy_qc = qc.copy()
            noisy_qc = self.apply_depolarization(noisy_qc)
            noisy_qubits.append(noisy_qc)
        
        return noisy_qubits, lost_indices
    
    def reset(self):
        """Reset noise statistics."""
        self.lost_qubits = 0


# Test
if __name__ == "__main__":
    from bb84_protocol import BB84Protocol
    
    print("Testing Noise Models...")
    
    # Create BB84 protocol
    bb84 = BB84Protocol(n_qubits=1000)
    qubits = bb84.alice_prepare_qubits()
    
    # Apply noise
    noise = NoiseModel(depolarization_prob=0.1, photon_loss_prob=0.2)
    noisy_qubits, lost_indices = noise.apply_noise_to_channel(qubits)
    
    print(f"Original qubits: {len(qubits)}")
    print(f"Lost qubits: {len(lost_indices)}")
    print(f"Remaining qubits: {len(noisy_qubits)}")
    print(f"Loss rate: {len(lost_indices)/len(qubits)*100:.1f}%")
